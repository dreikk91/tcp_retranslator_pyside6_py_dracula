from PySide6.QtCore import *
from PySide6.QtNetwork import *
from common.helpers import split_message_stream, SurGard, parse_surguard_message
from common.logger_config import logger
from common.sql_part import insert_into_buffer, insert_event, insert_into_buffer_sync, insert_event_sync, create_buffer_table_sync
from common.yaml_config import YamlConfig


MSG_END = b"\x14"
MSG_ACK = b"\x06"
MSG_NAK = b"\x15"
HEARTBEAT = "1011" + (" " * 11) + "@" + (" " * 4)


class MyTcpServer(QObject):
    def __init__(self, signals, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.server = QTcpServer(self)
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        create_buffer_table_sync()
        self.host = self.config["server"]["host"]
        self.port = self.config["server"]["port"]
        self.clients = []
        self.setup_keepalive_timer()

    def setup_keepalive_timer(self):
        self.keepalive_timer = QTimer(self)
        self.keepalive_timer.timeout.connect(self.send_keepalive)
        self.keepalive_timer.start(self.config["other"]["keepalive"]* 1000)  # відправляти keepalive кожні 50 секунд

    def run_server(self):
        if not self.server.listen(QHostAddress.Any, self.port):
            logger.info("Could not start server")
            self.signals.log_data.emit("Could not start server")

        self.server.newConnection.connect(self.handle_new_connection)

    def handle_new_connection(self):
        client = self.server.nextPendingConnection()
        self.clients.append(client)
        client.readyRead.connect(self.handle_ready_read)
        client.disconnected.connect(self.handle_disconnected)
        logger.info(f"New client connected: {client.peerAddress().toString()}:{client.peerPort()}")
        self.signals.log_data.emit(f"New client connected: {client.peerAddress().toString()}:{client.peerPort()}")

    def handle_ready_read(self):
        sender = self.sender()
        if sender in self.clients:
            data = sender.readAll()
            logger.info(f"Received data from {sender.peerAddress().toString()}:{sender.peerPort()} {data}")
            self.signals.log_data.emit(f"Received data from {sender.peerAddress().toString()}:{sender.peerPort()} {data}")
            self._process_message_stream(data)

    def _process_message_stream(self, data):
        sender = self.sender()
        for msg in split_message_stream(bytes(data)):
            sg = SurGard(msg)
            message = msg.decode().strip()
            if sg.is_valid():

                self.signals.log_data.emit(f"{message} append to queue")
                insert_into_buffer_sync(message)
                logger.info(f"{message} append to queue")
                sg_message = parse_surguard_message(message)
                insert_event_sync(sg_message, f'{sender.peerAddress().toString()}:{sender.peerPort()}')
                self.signals.data_receive.emit(f'{sender.peerAddress().toString()}:{sender.peerPort()}', msg.decode()
                )
            else:
                logger.error(f"Invalid message format {msg} {len(data)} send NAK")
                self.signals.log_data.emit(
                    f"Invalid message format {msg} {len(data)} send NAK"
                )
                sender.write(MSG_NAK)

    def handle_disconnected(self):
        sender = self.sender()
        if sender in self.clients:
            self.clients.remove(sender)
            sender.deleteLater()
            logger.info(f"Client disconnected: {sender.peerAddress().toString()}:{sender.peerPort()}")
            self.signals.log_data.emit(f"Client disconnected: {sender.peerAddress().toString()}:{sender.peerPort()}")

    def send_keepalive(self):
        for client in self.clients:
            client.write(MSG_END)
            logger.info(f'Send keepalive to  {client.peerAddress().toString()}:{client.peerPort()})')
            self.signals.log_data.emit(f'Send keepalive to  {client.peerAddress().toString()}:{client.peerPort()})')

# if __name__ == "__main__":
#     import sys
#
#     app = QCoreApplication(sys.argv)
#     server = MyTcpServer()
#     sys.exit(app.exec())