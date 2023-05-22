import asyncio
from PySide6.QtCore import QThread

# from common.logger_config import logger
from database.sql_part_postgres import create_buffer_table_sync
from common.yaml_config import YamlConfig
from net.retranslator_asyncio.tcp_server import TCPServer
from net.retranslator_asyncio.tcp_client import TCPClient
import logging
logger = logging.getLogger(__name__)

class RetranslatorThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.signals = signals
        self.server = TCPServer(self.signals)
        self.client = TCPClient(
            self.config["client"]["host"], self.config["client"]["port"], self.signals
        )
        self.client.retry_count = 0
        self.server_task = None
        self.client_task = None
        self.keepalive_task = None
        self.check_connection_status_task = None
        self.cnt = 0
        self.tasks = []

        # self.cs = ConnectionState()

    def run(self) -> None:
        logger.info("Worker data receiver start")
        # self.signals.stop_signal.connect(self.stop)
        self.signals.log_data.emit("Worker data receiver start")
        try:
            # with asyncio.Runner() as self.runner:
            #     self.runner.run(self.setup_tasks())
            asyncio.run(self.setup_tasks(), debug=True)
        except KeyboardInterrupt:
            print("Server and client stopped by user")
            self.signals.log_data.emit("Server and client stopped by user")

    def stop(self):
        pass
        # if self.cnt >= 30:
        #     for task in self.group:
        #         self.cnt = 0
        #         task.cancel()
        #
        # self.cnt +=1

    async def setup_tasks(self):
        # await create_buffer_table()
        create_buffer_table_sync()
        self.tasks.append(asyncio.create_task(self.server.run()))
        self.tasks.append(asyncio.create_task(self.client.start_tcp_client()))
        self.tasks.append(asyncio.create_task(self.server.keepalive()))
        # self.tasks.append(asyncio.create_task(self.server.check_connection_state()))
        # self.tasks.append(asyncio.create_task(commit_every_second()))
        self.group = asyncio.gather(*self.tasks, return_exceptions=True)
        await self.group

