import asyncio
from asyncio import Event
from typing import Any, Set, Union

from common.helpers import split_message_stream, SurGard, parse_surguard_message
from common.read_events_name_from_json import get_event_from_json
from database.sql_part_postgres_sync import insert_into_buffer_sync, insert_event_sync, insert_into_buffer_async
# from database.sql_part_sqlite import insert_into_buffer_sync, insert_event_sync
from common.yaml_config import YamlConfig
import logging

logger = logging.getLogger(__name__)

MSG_END: bytes = b"\x14"
MSG_ACK: bytes = b"\x06"
MSG_NAK: bytes = b"\x15"

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
        ConnectionState.is_running.set()


    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
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
                    await self._send_ack(writer)

                # Розірвання з'єднання після закінчення обробки
                self._handle_client_disconnect(writer)
        except (ConnectionResetError, ConnectionError, OSError, asyncio.IncompleteReadError) as err:
            # Обробка винятків та виведення повідомлення про помилку
            logger.exception(err)
            self.signals.log_data.emit(str(err))
            self._handle_client_disconnect(writer)

    async def _check_connection_state(self) -> None:
        # Check the connection state
        if not ConnectionState.is_running.is_set():
            raise ConnectionError("Server is not running")

    async def _handle_new_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        # Обробка нового підключення клієнта
        await self._check_connection_state()
        self.clients.add(writer)
        logger.info(f"New client connected: {writer.get_extra_info('peername')}")
        self.signals.log_data.emit(f"New client connected: {writer.get_extra_info('peername')}")

    async def _read_from_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bytes:
        # Отримання даних від клієнта
        await self._check_connection_state()
        data = await self.read_until(reader)
        logger.info(f"{data} received {writer.get_extra_info('peername')}")
        self.signals.log_data.emit(f"{data} received from {writer.get_extra_info('peername')}")
        return data

    async def _process_message_stream(self, data: bytes, writer: asyncio.StreamWriter) -> None:
        # Обробка потоку повідомлень
        if data is not None:
            await self._check_connection_state()
            splited_data = split_message_stream(data)
            if not splited_data:
                # Помилка: некоректний формат повідомлення
                logger.error(f"Incorrect message format {data}, send NAK")
                writer.write(MSG_NAK) 
                await writer.drain()
            else:
                for msg in split_message_stream(data):
                    sg = SurGard(msg)
                    if not data:
                        break
                    message = msg.decode().strip()
                    if sg.is_valid():
                        # Додавання повідомлення до черги та обробка події
                        logger.info(f"{message} append to queue")
                        await Buffer.queue.put({"message": message, "ip": writer.get_extra_info('peername')})
                        event_code = f"{message[11]}{message[12:15]}"

                        event_message = get_event_from_json.read_events(event_code)
                        self.signals.data_receive.emit(
                            writer.get_extra_info("peername"), msg.decode(), event_message
                        )
                        self.signals.log_data.emit(f"Message accepted {msg} {len(data)} send ACK")
                    elif msg == b'1001           @    \x14':
                        logger.info("Receive periodic test by station")
                    else:
                        # Помилка: некоректний формат повідомлення
                        logger.error(f"Invalid message format {msg} {len(data)} send NAK")
                        self.signals.log_data.emit(f"Invalid message format {msg} {len(data)} send NAK")
                        writer.write(MSG_NAK)
                        await writer.drain()

    async def _send_ack(self, writer: asyncio.StreamWriter) -> None:
        # Відправка підтвердження
        await self._check_connection_state()
        writer.write(MSG_ACK)
        logger.info("send ACK")
        self.signals.log_data.emit("send ACK")
        await writer.drain()

    def _handle_client_disconnect(self, writer: asyncio.StreamWriter) -> None:
        # Обробка відключення клієнта
        if writer in self.clients:
            self.clients.remove(writer)
            logger.info(f"Client disconnected: {writer.get_extra_info('peername')}")
            self.signals.log_data.emit(f"Client disconnected: {writer.get_extra_info('peername')})")
            writer.close()

    @staticmethod
    async def read_until(
        reader: asyncio.StreamReader, separator: bytes = MSG_END, timeout: int = 3600
    ) -> bytes:
        # Читання даних до роздільника
        try:
            data = await asyncio.wait_for(reader.read(1024), timeout=timeout)
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
                for client in self.clients.copy():
                    try:
                        await asyncio.sleep(10)
                        client.write(b"\x01")
                        logger.info(f"send keep-alive to {client.get_extra_info('peername')}")
                        self.signals.log_data.emit(f"send keep-alive to {client.get_extra_info('peername')}")
                        await client.drain()

                    except ConnectionError as err:
                        logger.exception(f"Keepalive failed {err}")
                        self.clients.remove(client)

            await asyncio.sleep(self.keepalive_interval)

    async def write_from_buffer_to_db(self):
        while True:
            message_list = []
            ip_list = []
            sg_message_list = []
            while not Buffer.queue.empty():
                message = await Buffer.queue.get()
                sg_message = parse_surguard_message(message['message'])
                message_list.append(message['message'])
                ip_list.append(message['ip'])
                sg_message_list.append(sg_message)

            if len(message_list)>0:
                insert_into_buffer_sync(message_list)
            await asyncio.sleep(1)

            #
            # insert_event_sync(sg_message, message['ip'])
            # await asyncio.sleep(1)

    async def check_connection_state(self):
        while True:
            await asyncio.sleep(1)
            if not ConnectionState.server_is_running and self.server.is_serving():
                try:
                    logger.info("Stopping server")
                    self.server.close()
                    await self.server.wait_closed()
                    for writer in self.clients:
                        writer.close()
                        logger.info(
                            f'New client connected: {writer.get_extra_info("peername")}'
                        )
                    logger.info("The server is stopped")
                    ConnectionState.ready_for_closed = True
                except Exception as err:
                    logger.exception(err)

    async def run(self) -> None:
        # Запуск серверу
        while True:
            try:
                self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
                break
            except OSError as err:
                logger.exception(err)
                logger.info("Next try in 10 sec")
                await asyncio.sleep(10)

        async with self.server:
            logger.info(f"Server started on {self.host}:{self.port}")
            self.signals.log_data.emit(f"Server started on {self.host}:{self.port}")
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