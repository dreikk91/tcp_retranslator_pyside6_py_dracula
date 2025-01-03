import asyncio
import logging
from datetime import datetime

from common.custom_exception import InvalidPacketException
from common.helpers import split_message_stream, SurGard
from common.read_events_name_from_json import get_event_from_json
from net.retranslator_asyncio.server.check_connection import ConnectionState

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MSG_END: bytes = b"\x14"
MSG_ACK: bytes = b"\x06"
MSG_NAK: bytes = b"\x15"


class ProcessData:
    def __init__(self, message_queues):
        self.message_queues = message_queues

    async def read_data(self, reader, writer):
        try:
            data = await self._read_from_client(reader, writer)
            if data:
                process_result = await self._process_message_stream(data, writer)
                return process_result

        except asyncio.CancelledError as err:
            logger.warning(err)

    async def _process_message_stream(
        self, data: bytes, writer: asyncio.StreamWriter
    ) -> bool:
        process_result = False
        # Обробка потоку повідомлень
        try:
            if data is not None:
                await self._check_connection_state()
                splited_data = split_message_stream(data)
                if not splited_data:
                    # Помилка: некоректний формат повідомлення
                    logger.error(f"Incorrect message format {data}, send NAK")

                    await self.message_queues.log_message_queues.put(
                        f"Incorrect message format {data}, send NAK"
                    )
                    writer.write(MSG_NAK)
                        # await self._send_ack(writer)
                    await writer.drain()

                    process_result = False
                    # raise InvalidPacketException
                else:
                    for msg in split_message_stream(data):
                        sg = SurGard(msg)
                        if not data:
                            break
                        message = msg.decode().strip()
                        if message[0] == "1" and "@" in message and "\x14" in message:
                            logger.info("Receive periodic test by station")
                            # self.signals.log_data.emit("Receive periodic test by station")
                            # await self.message_queues.log_message_queues.put(
                            #     "Receive periodic test by station"
                            # )
                            await self._send_ack(writer)
                            process_result = True
                        elif sg.is_valid():
                            # Додавання повідомлення до черги та обробка події
                            logger.info(f"{message} append to queue")
                            # await self.message_queues.log_message_queues.put(
                            #     f"{message} append to queue"
                            # )
                            object_number = message[7:11]
                            self.update_object_activity(object_number)
                            await self.message_queues.queue.put(
                                {
                                    "message": message,
                                    "ip": writer.get_extra_info("peername"),
                                }
                            )
                            event_code = f"{message[11]}{message[12:15]}"

                            event_message = get_event_from_json.read_events(event_code)
                            # self.signals.data_receive.emit(
                            #     writer.get_extra_info("peername"),
                            #     msg.decode(),
                            #     event_message,
                            # )
                            self.incoming_msg = (
                                writer.get_extra_info("peername"),
                                msg.decode(),
                                event_message,
                            )
                            await self.message_queues.incoming_message_queues.put(
                                self.incoming_msg
                            )
                            # self.signals.log_data.emit(
                            #     f"Message accepted {msg} {len(data)} send ACK"
                            # )
                            # await self.message_queues.log_message_queues.put(
                            #     f"Message accepted {msg} {len(data)} send ACK"
                            # )
                            await self._send_ack(writer)
                            process_result = True
                        else:
                            # Помилка: некоректний формат повідомлення
                            logger.error(
                                f"Invalid message format {msg} {len(data)} send NAK"
                            )
                            # self.signals.log_data.emit(
                            #     f"Invalid message format {msg} {len(data)} send NAK"
                            # )
                            await self.message_queues.log_message_queues.put(
                                f"Invalid message format {msg} {len(data)} send NAK"
                            )
                            writer.write(MSG_NAK)
                            await writer.drain()
                            process_result = False
        except Exception as e:
            # Записати весь стек викликів разом з повідомленням про помилку
            logger.exception(f"An error occurred: {e}")
            process_result = False

        return process_result


    async def _read_from_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bytes:
        # Отримання даних від клієнта
        await self._check_connection_state()
        data = None
        if not self.message_queues.incoming_message_queues.full():
            try:
                data = await self._read_until(reader)
                logger.info(f"{data} received {writer.get_extra_info('peername')}")
                # self.signals.log_data.emit(
                #     f"{data} received from {writer.get_extra_info('peername')}"
                # )
                # await self.message_queues.log_message_queues.put(
                #     f"{data} received from {writer.get_extra_info('peername')}"
                # )
                return data
            except Exception as e:
                logger.exception(f"An error occurred while reading from the client: {e}")
                await self.message_queues.log_message_queues.put(f"An error occurred while reading from the client: {e}")
                await asyncio.sleep(0.1)
                return data

        else:
            await asyncio.sleep(0.1)

    @staticmethod
    async def _read_until(
        reader: asyncio.StreamReader, separator: bytes = MSG_END, timeout: int = 3600
    ) -> bytes:
        # Читання даних до роздільника
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=timeout)
            return data
        except (
            asyncio.exceptions.TimeoutError,
            asyncio.IncompleteReadError,
            asyncio.exceptions.LimitOverrunError,
        ) as ex:
            # Виняток: таймаут підключення або закриття клієнтом
            raise ConnectionError("Connection timeout or closed by client") from ex

    async def _send_ack(self, writer: asyncio.StreamWriter) -> None:
        # Відправка підтвердження
        await self._check_connection_state()
        writer.write(MSG_ACK)
        await writer.drain()
        logger.info("send ACK")
        # self.signals.log_data.emit("send ACK")
        # await self.message_queues.log_message_queues.put("send ACK")

    def _update_object_activity(self, object_number):
        timestamp = str(datetime.now())
        object_activity = (object_number, timestamp)
        self.message_queues.object_activity_queues.put_nowait(object_activity)

    def update_object_activity(self, object_number):
        timestamp = str(datetime.now())
        object_activity = (object_number, timestamp)
        self.message_queues.object_activity_queues.put_nowait(object_activity)

    async def _check_connection_state(self) -> None:
        # Check the connection state
        if not ConnectionState.is_running.is_set():
            raise ConnectionError("Server is not running")

