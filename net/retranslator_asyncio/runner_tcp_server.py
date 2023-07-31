import asyncio
from PySide6.QtCore import QThread

from common.message_queues import WorkWithQueues
# from common.logger_config import logger
from database.sql_part_sync import create_buffer_table_sync
from common.yaml_config import YamlConfig
from net.retranslator_asyncio.tcp_server import TCPServer
from net.retranslator_asyncio.eventforwarder import EventForwarder
import logging

logger = logging.getLogger(__name__)


class TCPServerThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.signals = signals
        self.server = TCPServer(self.signals)
        self.server_task = None
        self.keepalive_task = None
        self.check_connection_status_task = None
        self.cnt = 0
        self.tasks = []
        self.loop = asyncio.get_event_loop()
        self.work_with_queues = WorkWithQueues(self.signals)

    def run(self) -> None:
        logger.info("Worker data receiver start")
        # self.signals.stop_signal.connect(self.stop)
        self.signals.log_data.emit("Worker data receiver start")
        try:
            # with asyncio.Runner() as self.runner:
            #     self.runner.run(self.setup_tasks())
            # asyncio.run(self.setup_tasks(), debug=True)
            self.loop.run_until_complete(self.setup_tasks())
        except KeyboardInterrupt:
            print("Server and client stopped by user")
            self.signals.log_data.emit("Server and client stopped by user")

    def stop(self):
        self.loop.call_soon_threadsafe(self._stop)

    def _stop(self):
        for task in self.tasks:
            task.cancel()

    async def setup_tasks(self):
        # await create_buffer_table()
        # create_buffer_table_sync()
        self.tasks.append(asyncio.create_task(self.server.run()))
        self.tasks.append(asyncio.create_task(self.server.write_from_buffer_to_db()))
        self.tasks.append(asyncio.create_task(self.server.keepalive()))
        self.tasks.append(asyncio.create_task(self.server.check_connection_state()))
        # self.tasks.append(asyncio.create_task(self.work_with_queues.write_from_queue_to_incoming_window()))
        # self.tasks.append(asyncio.create_task(self.work_with_queues.write_from_queue_to_outgoing_window()))
        # self.tasks.append(asyncio.create_task(self.work_with_queues.write_from_queue_to_log_window()))
        # self.tasks.append(asyncio.create_task(self.work_with_queues.write_from_queue_to_object_activity_window()))
        self.group = asyncio.gather(*self.tasks)

        try:
            await self.group
        except asyncio.CancelledError:
            print("Tasks cancelled")
