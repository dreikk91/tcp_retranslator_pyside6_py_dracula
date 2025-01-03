import asyncio
import logging
from typing import Set

from common.custom_exception import InvalidPacketException
from common.message_queues import MessageQueues
from common.yaml_config import YamlConfig
from net.retranslator_asyncio.server.check_connection import ConnectionState
from net.retranslator_asyncio.server.process_data import ProcessData

logger = logging.getLogger(__name__)

GLOBAL_DEBUG=False

class ClientHandler:
    def __init__(self) -> None:
        self.clients: Set[asyncio.StreamWriter] = set()
        self.message_queues = MessageQueues
        self.process_data = ProcessData(self.message_queues)
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.lock = asyncio.Lock()

        self.keepalive_interval: int = self.config["other"]["keepalive"]

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        # Обробка клієнтського з'єднання
        try:
            # Перевірка стану підключення
            print(f"handle_client_connection state is running {ConnectionState.is_running.is_set()}")
            if not ConnectionState.is_running.is_set():
                # Розірвання з'єднання, якщо сервер неактивний
                await self._handle_client_disconnect(writer)
            else:
                # Обробка нового клієнта
                await self._handle_new_client(reader, writer)
                # Отримання даних від клієнта та їх обробка
                while ConnectionState.is_running.is_set() and not writer.is_closing():
                    process_result = await self.process_data.read_data(reader, writer)
                    if process_result == False:
                        await self._handle_client_disconnect(writer)
                    # await self._send_ack(writer)

                # Розірвання з'єднання після закінчення обробки
                await self._handle_client_disconnect(writer)
        except (
            ConnectionResetError,
            ConnectionError,
            OSError,
            asyncio.IncompleteReadError,
            InvalidPacketException
        ) as err:
            await self._handle_error(writer, err)

    async def _handle_new_client(
            self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        async with self.lock:
            await self._check_connection_state()
            self.clients.add(writer)
            logger.error(f"New client connected: {writer.get_extra_info('peername')}")
            await self.message_queues.log_message_queues.put(
                f"New client connected: {writer.get_extra_info('peername')}"
            )

    async def _handle_client_disconnect(self, writer: asyncio.StreamWriter) -> None:
        async with self.lock:
            if writer in self.clients:
                self.clients.remove(writer)
                logger.error(f"Client disconnected: {writer.get_extra_info('peername')}")
                await self.message_queues.log_message_queues.put(
                    f"Client disconnected: {writer.get_extra_info('peername')})"
                )
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()


    async def _handle_error(
        self, writer: asyncio.StreamWriter, error: Exception
    ) -> None:
        logger.error(error)
        await self.message_queues.log_message_queues.put(str(error))
        await self._handle_client_disconnect(writer)


    async def _check_connection_state(self) -> None:
        # Check the connection state
        if not ConnectionState.is_running.is_set():
            raise ConnectionError("Server is not running")
