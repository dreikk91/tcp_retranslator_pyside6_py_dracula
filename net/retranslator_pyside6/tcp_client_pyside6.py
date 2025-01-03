from PySide6.QtCore import *
from PySide6.QtNetwork import *

from database.sql_part_postgres import select_from_buffer_sync, delete_from_buffer_sync
from common.yaml_config import YamlConfig
from common.logger_config import logger


class TcpClient(QObject):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.host = self.config["client"]["host"]
        self.port = self.config["client"]["port"]

        self.check_db_timer = QTimer(self)
        self.check_db_timer.timeout.connect(self.read_messages_from_buffer)
        self.check_db_timer.setInterval(10)

        self.tcp_socket = QTcpSocket(self)
        self.tcp_socket.readyRead.connect(self.readData)
        self.tcp_socket.errorOccurred.connect(self.onErrorOccurred)
        self.tcp_socket.connected.connect(self.connected)
        self.tcp_socket.disconnected.connect(self.disconnected)

        self.setup_connection_timers()

        # self.connect_to_host(self.host, self.port)

    def setup_connection_timers(self):
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setInterval(5000)
        self.reconnect_timer.timeout.connect(self.reconnect_to_server)

        self.timeout_timer = QTimer(self)
        self.timeout_timer.setInterval(10000)
        self.timeout_timer.timeout.connect(self.handle_timeout)

    def connected(self):
        logger.info(f"Connected to {self.host}:{self.port}")
        self.signals.log_data.emit(f"Connected to {self.host}:{self.port}")
        self.timeout_timer.stop()
        self.reconnect_timer.stop()
        self.check_db_timer.start()

    def disconnected(self):
        logger.info(f"Disconnected from {self.host}:{self.port}")
        self.signals.log_data.emit(f"Disconnected from {self.host}:{self.port}")
        self.tcp_socket.close()
        self.check_db_timer.stop()
        self.reconnect_timer.start()

    def connect_to_host(self, host, port):
        self.tcp_socket.connectToHost(host, port)
        self.timeout_timer.start()
        print(self.tcp_socket.state())

    def reconnect_to_server(self):
        if not self.tcp_socket.isOpen():
            self.tcp_socket.connectToHost(self.host, self.port)
            self.timeout_timer.start()
            logger.info("Trying to reconnect to server...")
            self.signals.log_data.emit("Trying to reconnect to server...")

    def handle_timeout(self):
        if self.tcp_socket.state() != QTcpSocket.ConnectedState:
            self.tcp_socket.disconnectFromHost()
            logger.error("Connection timed out.")
            self.signals.log_data.emit("Connection timed out.")
            self.tcp_socket.close()
            self.reconnect_to_server()

    def readData(self):
        data = self.tcp_socket.readAll()
        logger.info(f"Received response: {data}")
        self.signals.log_data.emit(f"Received response: {data}")

    def send_data(self, data):
        self.tcp_socket.write(data)
        self.tcp_socket.flush()
        logger.info(f"Sent data: {data}")
        self.signals.log_data.emit(f"Sent data: {data}")
        self.signals.data_send.emit(
            f"{self.tcp_socket.peerAddress().toString()}:{self.tcp_socket.peerPort()}",
            data.decode(),
        )

    def displayError(self, socketError):
        if socketError == QTcpSocket.RemoteHostClosedError:
            return

        logger.error(f"Error: {self.tcp_socket.errorString()}")
        self.signals.log_data.emit(f"Error: {self.tcp_socket.errorString()}")

    def onErrorOccurred(self, error):
        logger.info(f"Error occurred: {error}")
        self.signals.log_data.emit(f"Error occurred: {error}")

    def read_messages_from_buffer(self):
        row = select_from_buffer_sync()
        if row is not None:
            logger.info(f"Send {row.message.encode()}")
            self.signals.log_data.emit(f"Send {row.message.encode()}")
            self.send_data(row.message.encode())
            delete_from_buffer_sync(row.id)
            logger.debug(f"Delete from buffer by id {row.id}")
            self.signals.log_data.emit(f"Delete from buffer by id {row.id}")


#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     client = TcpClient()
#     sys.exit(app.exec())
