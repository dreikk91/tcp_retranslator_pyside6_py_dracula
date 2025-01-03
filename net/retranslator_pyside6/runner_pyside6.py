from PySide6.QtCore import QThread

from common.yaml_config import YamlConfig
from net.retranslator_pyside6.tcp_client_pyside6 import TcpClient
from net.retranslator_pyside6.tcp_server_pyside6 import MyTcpServer
from common.logger_config import logger


class TCPServerThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.tcp_server = MyTcpServer(self.signals)

    def run(self) -> None:
        logger.info("Thread data receiver start")
        self.tcp_server.run_server()


class TCPClientThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.tcp_client = TcpClient(self.signals)
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.host = self.config["client"]["host"]
        self.port = self.config["client"]["port"]

    def run(self) -> None:
        logger.info("Thread data sender start")
        self.tcp_client.connect_to_host(self.host, self.port)
