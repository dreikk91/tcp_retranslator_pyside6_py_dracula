import datetime
import os

# os.environ["PYTHONASYNCIODEBUG"] = "1"
import asyncio
import sys
import traceback

from asyncio import StreamReader, StreamWriter, Queue, Task
from collections import defaultdict
from contextlib import suppress
from typing import DefaultDict, Dict

from PySide6.QtCore import QRunnable
from loguru import logger

from common.worker_signals import WorkerSignals
from common.helpers import split_message_stream, check_message_format
from common.yaml_config import YamlConfig

MSG_END = b"\x14"
MSG_ACK = b"\x06"
MSG_NAK = b"\x15"
HEARTBEAT = "1011" + (" " * 11) + "@" + (" " * 4)

CLIENT_RECEIVE_DATA_QUEUES: DefaultDict[StreamWriter, Queue] = defaultdict(Queue)

# Dictionary storing request messages to process
# RECEIVE_FROM_SERVER_QUEUE: Dict[StreamReader, Queue] = defaultdict(Queue)
# RECEIVE_FROM_CLIENT_QUEUE: Dict[StreamReader, Queue] = defaultdict(Queue)
# SEND_TO_SERVER_QUEUE: Dict[StreamWriter, Queue] = defaultdict(Queue)
# SEND_TO_CLIENT_QUEUE: Dict[StreamWriter, Queue] = defaultdict(Queue)

try:
    os.mkdir("log")
except FileExistsError as err:
    logger.info(err)
logger.add(
    sink="log/tcp_retranslator.log",
    enqueue=True,
    rotation="1 day",
    retention="4 months",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    compression="zip",
)


# logging.basicConfig(
#     filename="log/debug.log",
#     filemode="w",
#     format="%(name)s - %(levelname)s - %(message)s",
#     level=logging.DEBUG,
# )
# logging.basicConfig(
#     level=logging.DEBUG,  # <-- update to DEBUG
#     format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
#     datefmt="%H:%M:%S",
# )
# warnings.resetwarnings()
#
# logging.getLogger("asyncio").setLevel(logging.DEBUG)
# @logger.catch
class DataReceiver(QRunnable):
    def __init__(self):
        super(DataReceiver, self).__init__()
        self.message = None
        self.recv_from_server_task = None
        self.send_to_client_task = None
        self.addr = None
        self.send_to_server_task = None
        self.signals = WorkerSignals()
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()

        self.RECEIVE_FROM_SERVER_QUEUE: Dict[StreamReader, Queue] = defaultdict(Queue)
        self.RECEIVE_FROM_CLIENT_QUEUE: Dict[StreamReader, Queue] = defaultdict(Queue)
        self.SEND_TO_SERVER_QUEUE: Dict[StreamWriter, Queue] = defaultdict(Queue)
        self.SEND_TO_CLIENT_QUEUE: Dict[StreamWriter, Queue] = defaultdict(Queue)

    def run(self):
        logger.info("Worker data receiver start")
        asyncio.run(self.main())

    async def on_client_connection(
        self, server_reader: StreamReader, server_writer: StreamWriter
    ):
        try:
            client_reader, client_writer = await self.open_connect_to_server()
        except OSError as error:
            logger.debug(error)
            client_reader, client_writer = await self.open_connect_to_server()

        self.addr: str = server_writer.get_extra_info("peername")
        self.signals.log_data.emit(f"A new connection is established {self.addr}")
        logger.info(f"A new connection is established {self.addr}")

        self.send_to_server_task = asyncio.create_task(
            self.send_data_to_server(
                client_writer, server_writer, self.SEND_TO_SERVER_QUEUE[client_writer]
            )
        )
        self.send_to_client_task = asyncio.create_task(
            self.send_data_to_client(
                server_writer, self.SEND_TO_CLIENT_QUEUE[server_writer]
            )
        )
        # self.recv_from_server_task: Task[None] = asyncio.create_task(
        #     self.receive_data_from_server(
        #         client_reader,
        #         client_writer,
        #         server_writer,
        #         RECEIVE_FROM_SERVER_QUEUE[client_reader],
        #     )
        # )

        await self.SEND_TO_CLIENT_QUEUE[server_writer].put(MSG_NAK)
        try:
            while request := await server_reader.read(1024):
                logger.info(request)
                self.signals.log_data.emit(
                    f"Receiving message from client {request.decode()}"
                )
                if check_message_format(request):
                    current_time = datetime.datetime.now().strftime(
                        "%m/%d/%Y, %H:%M:%S"
                    )
                    self.message: bytes = request
                    addr = server_writer.get_extra_info("peername")
                    for msg in split_message_stream(self.message):
                        await self.SEND_TO_SERVER_QUEUE[client_writer].put(msg)
                        self.signals.data_receive.emit(addr, msg.decode(), current_time)

        except asyncio.CancelledError:
            logger.debug(f"Remote {self.addr} connection cancelled.")
        except asyncio.IncompleteReadError:
            logger.debug(f"Remote {self.addr} disconnected")
        except ConnectionResetError:
            logger.debug(f"Remote {self.addr} disconnected, connection reset")
        except OSError as err:
            logger.error(err)
        finally:
            logger.info(f"Remote {self.addr} closed")
            self.signals.log_data.emit(f"Remote {self.addr} closed")
            await self.SEND_TO_CLIENT_QUEUE[server_writer].put(None)
            await self.send_to_client_task
            del self.SEND_TO_CLIENT_QUEUE[server_writer]

            await self.SEND_TO_SERVER_QUEUE[client_writer].put(None)
            await self.send_to_server_task
            del self.SEND_TO_SERVER_QUEUE[client_writer]

    async def send_data_to_server(self, writer, server_writer, queue):
        while True:
            msg: bytes = await queue.get()
            if not msg:
                break
            try:
                writer.write(msg)
                await writer.drain()

                current_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                addr = writer.get_extra_info("peername")
                self.signals.data_send.emit(addr, msg.decode(), current_time)
                self.signals.log_data.emit(f"Send to server {msg.decode()}")
                await self.SEND_TO_CLIENT_QUEUE[server_writer].put(MSG_ACK)
                self.signals.log_data.emit(f"Send ACK message")

            except asyncio.CancelledError as error:
                logger.error("Task canceled", error)
            except ConnectionResetError as error:
                logger.debug(error)
                await asyncio.sleep(10)
                reader, writer = await self.open_connect_to_server()
                writer.write(msg)
                await writer.drain()
                logger.info(f"{msg} resend")

        logger.debug(
            f"Server writer is closing in send_data_to_server {writer.is_closing()}"
        )
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()

    async def receive_data_from_server(
        self, client_reader, client_writer, server_writer, queue
    ):
        while True:
            print(f"Client writer is closing {client_writer.is_closing()}")
            addr = server_writer.get_extra_info("peername")
            if client_writer.is_closing():
                break
            try:
                while request := await client_reader.read(1000):
                    logger.info(request)
                    self.signals.log_data.emit(
                        f"Receiving from server {request.decode()}, {addr}"
                    )
                    if not server_writer.is_closing():
                        await self.SEND_TO_CLIENT_QUEUE[server_writer].put(request)
                        print(self.SEND_TO_CLIENT_QUEUE[server_writer])
            except asyncio.CancelledError:
                logger.debug(f"Remote {addr} connection cancelled.")
            except asyncio.IncompleteReadError:
                logger.debug(f"Remote {addr} disconnected")
            except ConnectionResetError:
                logger.debug(f"Remote {addr} disconnected, connection reset")
            finally:
                logger.info(f"Remote {addr} closed")
                await self.SEND_TO_CLIENT_QUEUE[server_writer].put(None)

    async def send_data_to_client(self, writer, queue):
        with suppress(asyncio.CancelledError):
            while True:
                addr = writer.get_extra_info("peername")
                try:
                    msg: bytes = await queue.get()
                except asyncio.CancelledError:
                    continue

                if not msg:
                    break
                try:
                    writer.write(msg)
                    await writer.drain()
                    self.signals.log_data.emit(
                        f"Receiving from server {msg.decode()}, {addr}"
                    )
                except ConnectionResetError as error:
                    logger.debug(error)
                    reader, writer = await self.open_connect_to_server()
                    writer.write(msg)
                    await writer.drain()
                    logger.info(f"{msg} resend")
            logger.debug(
                f"Server writer is closing in send_data_to_client {writer.is_closing()}"
            )
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()

    async def open_connect_to_server(self):
        while True:
            conn = asyncio.open_connection(
                self.config["client"]["host"], self.config["client"]["port"]
            )
            logger.info(
                f'Connecting to server: {self.config["client"]["host"]}'
                f' on port: {self.config["client"]["port"]}'
            )
            try:
                reader, writer = await asyncio.wait_for(conn, 10)
                return reader, writer
            except ConnectionRefusedError as error:
                logger.debug(f"Remote server unavailable, {error}")
                logger.info("Reconnecting after 10 seconds")
                self.signals.log_data.emit(f"Remote server unavailable, {error}")
                await asyncio.sleep(10)
            except asyncio.TimeoutError as error:
                # logger.debug(f"Connection to  {host}:{port} timeout, {error}")
                logger.info("Reconnecting after 10 seconds")
                self.signals.log_data.emit(f"Remote server unavailable, {error}")
                await asyncio.sleep(10)

    async def send_ping_to_clients(self):
        address_list: list = []
        while True:
            # await asyncio.sleep(3)
            try:
                for writer in self.SEND_TO_CLIENT_QUEUE:
                    if not self.SEND_TO_CLIENT_QUEUE[writer].full():
                        # print("writer not full", SEND_QUEUES[writer].full())
                        # print("writer not empty", SEND_QUEUES[writer].empty())
                        if writer.get_extra_info("peername") not in address_list:
                            await self.SEND_TO_CLIENT_QUEUE[writer].put(MSG_END)
                            address_list.append(writer.get_extra_info("peername"))
                            logger.info(
                                f"Add periodic test to writer {writer.get_extra_info('peername')}"
                            )
                address_list = []
                await asyncio.sleep(60)
            except RuntimeError as err:
                logger.debug(err)

    async def main(self):
        server = await asyncio.start_server(
            self.on_client_connection,
            host=self.config["server"]["host"],
            port=self.config["server"]["port"],
        )
        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        check_connection = asyncio.create_task(self.send_ping_to_clients())
        logger.info(f"Serving on {addrs}")
        async with server:
            await server.serve_forever()
            await check_connection


# if __name__ == "__main__":
#     with logger.catch():
#         try:
#             asyncio.run(main())
#         except KeyboardInterrupt:
#             print("\r\nBye!")
