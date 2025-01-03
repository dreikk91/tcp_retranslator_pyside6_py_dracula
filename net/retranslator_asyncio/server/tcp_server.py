import asyncio
import logging
from typing import Any, Union

from common.helpers import parse_surguard_message
from common.message_queues import MessageQueues

# from database.sql_part_sqlite import insert_into_buffer_sync, insert_event_sync
from common.yaml_config import YamlConfig
from database.sql_part_sync import (
    create_engine_and_session,
    insert_into_buffer_sync,
    check_connection,
)
from net.retranslator_asyncio.server.check_connection import ConnectionState
from net.retranslator_asyncio.server.client_hendler import ClientHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MSG_END: bytes = b"\x14"
MSG_ACK: bytes = b"\x06"
MSG_NAK: bytes = b"\x15"
HEARTBEAT: str = "1001           @    \x14"


class TCPServer:
    def __init__(self, signals: Any) -> None:
        # Ініціалізація серверу TCP з сигналами
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.host: str = self.config["server"]["host"]
        self.port: int = self.config["server"]["port"]
        self.signals = signals
        self.server: Union[None, asyncio.AbstractServer] = None
        self.objects_activity = {}
        ConnectionState.is_running.set()
        self.engine, self.Session = create_engine_and_session()
        self.message_queues = MessageQueues
        self.incoming_msg = ()
        self.heartbeat = "1010           @    \x14"
        self.client_handler = ClientHandler()
        self.clients = self.client_handler.clients

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        await self.client_handler.handle_client(reader, writer)

    async def write_from_buffer_to_db(self):
        while True:
            message_list = []
            ip_list = []
            sg_message_list = []
            if check_connection(self.engine):
                while not self.message_queues.queue.empty():
                    message = await self.message_queues.queue.get()
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

    async def check_connection_state(self):
        while True:
            await asyncio.sleep(1)
            if not ConnectionState.server_is_running:
                try:
                    logger.info("Stopping server")
                    await self.message_queues.log_message_queues.put("Stopping server")
                    for writer in self.clients:
                        writer.close()

                        logger.info(
                            f'Client disconnected: {writer.get_extra_info("peername")}'
                        )
                        await self.message_queues.log_message_queues.put(
                            f'Client disconnected:{writer.get_extra_info("peername")}'
                        )
                    self.clients.clear()
                    logger.info("The server is stopped")
                    await self.message_queues.log_message_queues.put(
                        "The server is stopped"
                    )
                    await self.message_queues.log_message_queues.put("Stopping server")
                    self.server.close()
                    await self.server.wait_closed()
                    ConnectionState.ready_for_closed = True
                except Exception as err:
                    logger.error(err)
                    await self.message_queues.log_message_queues.put(err)

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
        for writer in self.clients:
            writer.close()
        if self.server and self.server.is_serving():
            self.server.close()

        for writer in self.clients:
            writer.close()


# class Buffer:
#     queue = asyncio.Queue()
#     incoming_message_queues = asyncio.Queue()
#     outgoing_message_queues = asyncio.Queue()
#     log_message_queues = asyncio.Queue()
