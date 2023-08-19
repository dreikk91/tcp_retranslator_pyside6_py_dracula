import asyncio
import logging
from asyncio import Event
from datetime import datetime
from typing import Any, Set, Union

from common.helpers import split_message_stream, SurGard, parse_surguard_message
from common.read_events_name_from_json import get_event_from_json
from common.message_queues import MessageQueues
from database.sql_part_sync import (
    create_engine_and_session,
    insert_into_buffer_sync,
    check_connection,
)

# from database.sql_part_sqlite import insert_into_buffer_sync, insert_event_sync
from common.yaml_config import YamlConfig


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MSG_END: bytes = b"\x14"
MSG_ACK: bytes = b"\x06"
MSG_NAK: bytes = b"\x15"
HEARTBEAT: str = '1001           @    \x14'


class TCPServer:
    def __init__(self, signals: Any) -> None:
        # Ініціалізація серверу TCP з сигналами
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.host: str = self.config["server"]["host"]
        self.port: int = self.config["server"]["port"]
        self.keepalive_interval: int = self.config["other"]["keepalive"]
        self.clients: Set[asyncio.StreamWriter] = set()
        self.signals = signals
        self.server: Union[None, asyncio.AbstractServer] = None
        self.objects_activity = {}
        ConnectionState.is_running.set()
        self.engine, self.Session = create_engine_and_session()
        self.message_queues = MessageQueues
        self.incoming_msg = ()
        self.heartbeat = '1010           @    \x14'

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        # Обробка клієнтського з'єднання
        try:
            # Перевірка стану підключення
            if not ConnectionState.is_running.is_set():
                # Розірвання з'єднання, якщо сервер неактивний
                self._handle_client_disconnect(writer)
            else:
                # Обробка нового клієнта
                await self._handle_new_client(reader, writer)
                # Отримання даних від клієнта та їх обробка
                while ConnectionState.is_running.is_set():
                    data = await self._read_from_client(reader, writer)
                    await self._process_message_stream(data, writer)
                    # await self._send_ack(writer)

                # Розірвання з'єднання після закінчення обробки
                self._handle_client_disconnect(writer)
        except (
            ConnectionResetError,
            ConnectionError,
            OSError,
            asyncio.IncompleteReadError,
        ) as err:
            # Обробка винятків та виведення повідомлення про помилку
            logger.error(err)
            await self.message_queues.log_message_queues.put(str(err))
            # self.signals.log_data.emit(str(err))
            self._handle_client_disconnect(writer)

    async def _check_connection_state(self) -> None:
        # Check the connection state
        if not ConnectionState.is_running.is_set():
            raise ConnectionError("Server is not running")

    async def _handle_new_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        # Обробка нового підключення клієнта
        await self._check_connection_state()
        self.clients.add(writer)
        logger.info(f"New client connected: {writer.get_extra_info('peername')}")
        # self.signals.log_data.emit(
        #     f"New client connected: {writer.get_extra_info('peername')}"
        # )
        await self.message_queues.log_message_queues.put(
            f"New client connected: {writer.get_extra_info('peername')}"
        )

    async def _read_from_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bytes:
        # Отримання даних від клієнта
        await self._check_connection_state()
        if not self.message_queues.incoming_message_queues.full():
            data = await self.read_until(reader)
            logger.info(f"{data} received {writer.get_extra_info('peername')}")
            # self.signals.log_data.emit(
            #     f"{data} received from {writer.get_extra_info('peername')}"
            # )
            await self.message_queues.log_message_queues.put(
                f"{data} received from {writer.get_extra_info('peername')}"
            )
            return data
        else:
            await asyncio.sleep(0.1)

    async def _process_message_stream(
        self, data: bytes, writer: asyncio.StreamWriter
    ) -> None:
        # Обробка потоку повідомлень
        if data is not None:
            await self._check_connection_state()
            splited_data = split_message_stream(data)
            if not splited_data:
                # Помилка: некоректний формат повідомлення
                logger.debug(f"Incorrect message format {data}, send NAK")
                await self.message_queues.log_message_queues.put(
                    f"Incorrect message format {data}, send NAK"
                )
                writer.write(MSG_NAK)
                # await self._send_ack(writer)
                await writer.drain()
            else:
                for msg in split_message_stream(data):
                    sg = SurGard(msg)
                    if not data:
                        break
                    message = msg.decode().strip()
                    if message[0] == "1" and "@" in message and "\x14" in message:
                        logger.info("Receive periodic test by station")
                        # self.signals.log_data.emit("Receive periodic test by station")
                        await self.message_queues.log_message_queues.put(
                            "Receive periodic test by station"
                        )
                        await self._send_ack(writer)
                    elif sg.is_valid():
                        # Додавання повідомлення до черги та обробка події
                        logger.info(f"{message} append to queue")
                        await self.message_queues.log_message_queues.put(
                            f"{message} append to queue"
                        )
                        object_number = message[7:11]
                        self.update_object_activity(object_number)
                        await Buffer.queue.put(
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
                        self.incoming_msg = (writer.get_extra_info("peername"),  msg.decode(), event_message)
                        await self.message_queues.incoming_message_queues.put(self.incoming_msg)
                        # self.signals.log_data.emit(
                        #     f"Message accepted {msg} {len(data)} send ACK"
                        # )
                        await self.message_queues.log_message_queues.put(
                            f"Message accepted {msg} {len(data)} send ACK"
                        )
                        await self._send_ack(writer)
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

    async def _send_ack(self, writer: asyncio.StreamWriter) -> None:
        # Відправка підтвердження
        await self._check_connection_state()
        writer.write(MSG_ACK)
        logger.info("send ACK")
        # self.signals.log_data.emit("send ACK")
        await self.message_queues.log_message_queues.put("send ACK")
        await writer.drain()

    def _handle_client_disconnect(self, writer: asyncio.StreamWriter) -> None:
        # Обробка відключення клієнта
        if writer in self.clients:
            self.clients.remove(writer)
            logger.info(f"Client disconnected: {writer.get_extra_info('peername')}")
            # self.signals.log_data.emit(
            #     f"Client disconnected: {writer.get_extra_info('peername')})"
            # )
            self.message_queues.log_message_queues.put_nowait(
                f"Client disconnected: {writer.get_extra_info('peername')})"
            )
            writer.close()

    @staticmethod
    async def read_until(
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

    async def keepalive(self) -> None:
        # Відправка пакетів підтримки з'єднання
        while True:
            if ConnectionState.is_running.is_set():
                for writer in self.clients.copy():
                    try:
                        await asyncio.sleep(10)
                        writer.write(b"\x01")
                        await writer.drain()
                        logger.info(
                            f"send keep-alive to {writer.get_extra_info('peername')}"
                        )
                        # self.signals.log_data.emit(
                        #     f"send keep-alive to {client.get_extra_info('peername')}"
                        # )
                        await self.message_queues.log_message_queues.put(
                            f"send keep-alive to {writer.get_extra_info('peername')}"
                        )

                    except ConnectionError as err:
                        self._handle_client_disconnect(writer)
                        logger.error(f"Keepalive failed {err}")
                        await self.message_queues.log_message_queues.put(
                            f"Keepalive failed {err}"
                        )
                        self._handle_client_disconnect(writer)
                        # self.clients.remove(client)

            await asyncio.sleep(self.keepalive_interval)

    def update_object_activity(self, object_number):
        timestamp = str(datetime.now())
        object_activity = (object_number, timestamp)
        self.message_queues.object_activity_queues.put_nowait(object_activity)
        # self.signals.objects_activity.emit(object_number, timestamp)

    # async def check_object_activity(object_number):
    #     last_event_time = self.objects_activity.get(object_number)
    #     if last_event_time is not None:
    #         current_time = datetime.now()
    #         time_difference = current_time - last_event_time
    #         if time_difference.total_seconds() > 600:  # 10 minutes
    #             # Відправити повідомлення про несправність об'єкта
    #             print(f"Object {object_number} is inactive for more than 10 minutes.")
    #     else:
    #         # Об'єкт не має жодної отриманої події
    #         print(f"Object {object_number} has no events.")

    async def write_from_buffer_to_db(self):
        while True:
            message_list = []
            ip_list = []
            sg_message_list = []
            if check_connection(self.engine):
                while not Buffer.queue.empty():
                    message = await Buffer.queue.get()
                    sg_message = parse_surguard_message(message["message"])
                    message_list.append(message["message"])
                    ip_list.append(message["ip"])
                    sg_message_list.append(sg_message)

                if len(message_list) > 0:
                    insert_into_buffer_sync(self.Session, message_list)
                await asyncio.sleep(1)
            else:
                logger.error("Connection to database not exist")
                await self.message_queues.log_message_queues.put(
                    "Connection to database not exist"
                )
                await asyncio.sleep(10)
                self.engine, self.Session = create_engine_and_session()

            #
            # insert_event_sync(sg_message, message['ip'])
            # await asyncio.sleep(1)

    async def check_connection_state(self):
        while True:
            await asyncio.sleep(1)
            if not ConnectionState.server_is_running and self.server.is_serving():
                try:
                    logger.info("Stopping server")
                    await self.message_queues.log_message_queues.put("Stopping server")
                    self.server.close()
                    await self.server.wait_closed()
                    for writer in self.clients:
                        writer.close()
                        logger.info(
                            f'New client connected: {writer.get_extra_info("peername")}'
                        )
                        await self.message_queues.log_message_queues.put(
                            f'New client connected: {writer.get_extra_info("peername")}'
                        )
                    logger.info("The server is stopped")
                    await self.message_queues.log_message_queues.put(
                        "The server is stopped"
                    )
                    ConnectionState.ready_for_closed = True
                except Exception as err:
                    logger.error(err)
                    await self.message_queues.log_message_queues.put(err)

    # async def write_from_queue_to_log_window(self) -> None:
    #     while True:
    #         if check_connection(self.engine):
    #             if not self.buffer.log_message_queues.empty():
    #                 log_message = await self.buffer.log_message_queues.get()
    #                 self.signals.log_data.emit(log_message)
    #                 logger.warning(f"message {log_message} get from buffer")
    #             else:
    #                 await asyncio.sleep(1)

    async def run(self) -> None:
        # Запуск серверу
        while True:
            try:
                logger.info("Starting TCP server")
                await self.message_queues.log_message_queues.put("Starting TCP server")
                self.server = await asyncio.start_server(
                    self.handle_client, self.host, self.port
                )
                break
            except OSError as err:
                logger.error(err)
                await self.message_queues.log_message_queues.put(err)
                logger.info("Next try in 10 sec")
                await self.message_queues.log_message_queues.put("Next try in 10 sec")
                await asyncio.sleep(10)

        async with self.server:
            logger.info(f"Server started on {self.host}:{self.port}")
            # self.signals.log_data.emit(f"Server started on {self.host}:{self.port}")
            await self.message_queues.log_message_queues.put(
                f"Server started on {self.host}:{self.port}"
            )
            await self.server.serve_forever()

    def stop(self) -> None:
        # Зупинка серверу
        ConnectionState.is_running.clear()
        if self.server and self.server.is_serving():
            self.server.close()
        for writer in self.clients:
            writer.close()


class ConnectionState:
    # Клас, що відстежує стан підключення серверу
    is_running: Event = asyncio.Event()
    server_is_running = True
    ready_for_closed = False


class Buffer:
    queue = asyncio.Queue()
    incoming_message_queues = asyncio.Queue()
    outgoing_message_queues = asyncio.Queue()
    log_message_queues = asyncio.Queue()
