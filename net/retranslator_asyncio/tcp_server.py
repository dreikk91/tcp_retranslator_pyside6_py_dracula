import asyncio
from asyncio import Event
from typing import Set, Any

from common.helpers import split_message_stream, SurGard, parse_surguard_message
from common.read_events_name_from_json import get_event_from_json
# from common.logger_config import logger
from common.sql_part import insert_into_buffer_sync, insert_event_sync
from common.yaml_config import YamlConfig
import logging
logger = logging.getLogger(__name__)

MSG_END = b"\x14"
MSG_ACK = b"\x06"
MSG_NAK = b"\x15"
HEARTBEAT = "1011" + (" " * 11) + "@" + (" " * 4)


class TCPServer:
    def __init__(self, signals):
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config: Any = self.yc.config_open()
        self.host: Any = self.config["server"]["host"]
        self.port: Any = self.config["server"]["port"]
        self.keepalive_interval: Any = self.config["other"]["keepalive"]
        self.clients: Set[asyncio.StreamWriter] = set()
        self.signals: Any = signals
        self.server = None
        ConnectionState.is_running.set()

    @staticmethod
    async def _check_connection_state():
        if not ConnectionState.is_running.is_set():
            raise ConnectionError("Connection is closed")

    async def check_connection_state(self):
        pass
        # while True:
        #     await asyncio.sleep(1)
        #     if not ConnectionState.is_runnung.is_set() and self.server.is_serving():
        #         try:
        #             logger.info("Stopping the server...")
        #             self.server.close()
        #             await self.server.wait_closed()
        #             for writer in self.clients:
        #                 writer.close()
        #                 logger.info(
        #                     f'New client connected: {writer.get_extra_info("peername")}'
        #                 )
        #             logger.info("The server is stopped")
        #             print(ConnectionState.is_runnung.is_set())
        #         except Exception as e:
        #             logger.error(e)
        #     elif (
        #         self.server.is_serving() == False
        #         and ConnectionState.is_runnung.is_set()
        #     ):
        #         print(ConnectionState.is_runnung.is_set())
        #         logger.info("Starting the server...")
        #         await asyncio.sleep(0.1)
        #         await asyncio.wait_for(self.run(), 2)
        #         await asyncio.sleep(0.1)

    async def handle_client(self, reader, writer):
        try:
            if not ConnectionState.is_running.is_set():

                self._handle_client_disconnect(writer)
            else:
                await self._handle_new_client(reader, writer)
                while ConnectionState.is_running.is_set():
                    data: bytes = await self._read_from_client(reader, writer)
                    await self._process_message_stream(data, writer)
                    await self._send_ack(writer)
                    await asyncio.sleep(0.001)
                self._handle_client_disconnect(writer)
        except (
            ConnectionResetError,
            ConnectionError,
            OSError,
            asyncio.exceptions.IncompleteReadError,
        ) as err:
            logger.exception(err)
            self.signals.log_data.emit(str(err))
            self._handle_client_disconnect(writer)

    async def _handle_new_client(self, reader, writer):
        await self._check_connection_state()
        self.clients.add(writer)
        logger.info(f'New client connected: {writer.get_extra_info("peername")}')
        self.signals.log_data.emit(
            f'New client connected: {writer.get_extra_info("peername")}'
        )

    async def _read_from_client(self, reader, writer):
        await self._check_connection_state()
        data = await self.read_until(reader)
        logger.info(f"{data} received {writer.get_extra_info('peername')}")
        self.signals.log_data.emit(f"{data} received from {writer.get_extra_info('peername')}")
        return data

    async def _process_message_stream(self, data: bytes, writer):
        if data is not None:
            await self._check_connection_state()
            splited_data = split_message_stream(data)
            if not splited_data:
                logger.error(splited_data)
            else:
                for msg in split_message_stream(data):
                    sg = SurGard(msg)
                    if not data:
                        break
                    message: str = msg.decode().strip()
                    if sg.is_valid():
                        logger.info(f"{message} append to queue")
                        self.signals.log_data.emit(f"{message} append to queue")
                        insert_into_buffer_sync(message)

                        # await insert_into_buffer(message)
                        sg_message: dict = parse_surguard_message(message)
                        insert_event_sync(sg_message, writer.get_extra_info("peername"))
                        # await insert_event(sg_message, writer.get_extra_info("peername"))
                        event_code: str = f'{message[11]}{message[12:15]}'
                        # event_type = message[11]
                        # event_code = message[12:15]
                        # allcodes = [*event_guard, *event_disguard, *event_alarm, *event_ok, *other_events]
                        # for i in range(1000000):
                        #     for code in allcodes:
                        #         event_code = code
                        #         event_message: dict = get_event_from_json.read_events(event_code)
                        #         self.signals.data_receive.emit(
                        #             writer.get_extra_info("peername"), msg.decode(), event_message
                        #         )
                        #         self.signals.log_data.emit(
                        #             f"Invalid message format {msg} {len(data)} send NAK"
                        #         )
                        #         await asyncio.sleep(0.01)
                        #     i += i
                        event_message: dict = get_event_from_json.read_events(event_code)
                        self.signals.data_receive.emit(
                            writer.get_extra_info("peername"), msg.decode(), event_message
                        )
                        self.signals.log_data.emit(
                            f"Invalid message format {msg} {len(data)} send NAK"
                        )
                    else:
                        logger.error(f"Invalid message format {msg} {len(data)} send NAK")
                        self.signals.log_data.emit(
                            f"Invalid message format {msg} {len(data)} send NAK"
                        )
                        writer.write(MSG_NAK)

    async def _send_ack(self, writer):
        await self._check_connection_state()
        writer.write(MSG_ACK)
        logger.info("send ACK")
        self.signals.log_data.emit("send ACK")
        await writer.drain()
        # await asyncio.sleep(0.05)

    def _handle_client_disconnect(self, writer):
        if writer in self.clients:
            self.clients.remove(writer)
            logger.info(f'Client disconnected: {writer.get_extra_info("peername")}')
            self.signals.log_data.emit(
                f'Client disconnected: {writer.get_extra_info("peername")})'
            )
            writer.close()

    @staticmethod
    async def read_until(reader, separator=MSG_END, timeout=3600):
        try:
            data = await asyncio.wait_for(
                reader.readuntil(separator=separator), timeout=timeout
            )
            return data
        except asyncio.exceptions.TimeoutError as ex:
            raise ConnectionError("Connection timeout") from ex
        except asyncio.IncompleteReadError as ex:
            raise ConnectionError("Connection closed by client") from ex
        except asyncio.exceptions.LimitOverrunError as ex:
            raise ConnectionError("Separator is not found, and chunk exceed the limit") from ex

    async def keepalive(self):
        while True:
            if ConnectionState.is_running.is_set():
                for client in self.clients:
                    # Надсилаємо keepalive кожні 30 секунд
                    try:
                        client.write(b"\x01")
                        logger.info(
                            f'send keep-alive to {client.get_extra_info("peername")}'
                        )
                        self.signals.log_data.emit(
                            f'send keep-alive to {client.get_extra_info("peername")}'
                        )
                        await client.drain()
                    except ConnectionError as err:
                        logger.exception(f"Keepalive failed {err}")
                        self.clients.remove(client)

            await asyncio.sleep(self.keepalive_interval)

    async def run(self):
        # Створюємо серверний об'єкт
        try:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
        except OSError as err:
            logger.exception(err)
            logger.info('Next try in 10 sec')
            await asyncio.sleep(10)
            await self.run()
        # asyncio.create_task(self.keepalive())

        # Запускаємо async-задачі для обробки повідомлень та keepalive
        await asyncio.sleep(0)
        # Чекаємо на підключення
        async with self.server:
            logger.info(f"Server started on {self.host}:{self.port}")
            self.signals.log_data.emit(f"Server started on {self.host}:{self.port}")
            await asyncio.sleep(0.001)
            await self.server.serve_forever()

    def stop(self):
        print(ConnectionState.is_running)
        ConnectionState.is_running.clear()
        if self.server and self.server.is_serving():
            self.server.close()
        for writer in self.clients:
            writer.close()


class ConnectionState:
    # is_running = True

    is_running: Event = asyncio.Event()
