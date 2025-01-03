import asyncio
import logging
import signal
from PySide6.QtCore import QThread

# from common.logger_config import logger
from common.yaml_config import YamlConfig
from net.retranslator_asyncio.event_forwarder.eventforwarder import EventForwarder

logger = logging.getLogger(__name__)


class EventForwarderThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.signals = signals
        # self.server = TCPServer(self.signals)
        self.client = EventForwarder(
            self.config["client"]["host"], self.config["client"]["port"], self.signals
        )
        self.client.retry_count = 0
        self.server_task = None
        self.client_task = None
        self.keepalive_task = None
        self.check_connection_status_task = None
        self.cnt = 0
        self.tasks = []
        self.loop = None

        # self.cs = ConnectionState()

    def run(self) -> None:
        logger.info("Worker data sender start")
        # self.signals.stop_signal.connect(self.stop)
        self.signals.log_data.emit("Worker data sender start")
        try:
            # with asyncio.Runner() as self.runner:
            #     self.runner.run(self.setup_tasks())
            # asyncio.run(self.setup_tasks(), debug=True)
            self.loop = asyncio.new_event_loop()
            self.loop.set_debug(False)
            self.loop.run_until_complete(self.setup_client_tasks())
        except KeyboardInterrupt:
            print("Server and client stopped by user")
            self.signals.log_data.emit("Server and client stopped by user")

    def stop(self):
        self.loop.call_soon_threadsafe(self._stop)


    def _stop(self):
        print(">> Cancelling tasks now")
        for task in asyncio.all_tasks():
            print(task)
            task.cancel()

        print(">> Done cancelling tasks")
        asyncio.get_event_loop().stop()
        self.loop = None

    async def setup_client_tasks(self):
        self.tasks.append(asyncio.create_task(self.client.start_tcp_client()))
        self.group = asyncio.gather(*self.tasks, return_exceptions=False)

        await self.group
