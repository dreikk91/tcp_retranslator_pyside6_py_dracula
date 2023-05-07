from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import QThread, QRunnable, QMetaObject, Qt, Signal
from PySide6.QtWidgets import QListWidgetItem
from loguru import logger
from sqlalchemy import insert, select, delete
from twisted.application import service
from twisted.internet import reactor, protocol, endpoints, defer
from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver

from common.worker_signals import WorkerSignals
from common.yaml_config import YamlConfig
from common.helpers import SurGard
from ui.ui_main_window import Ui_MainWindow

MSG_END = b"\x14"
MSG_ACK = b"\x06"
MSG_NAK = b"\x15"

HEARTBEAT = "1011" + (" " * 11) + "@" + (" " * 4)


# MESSAGE_RECEIVED_LIST: Deque = deque([])


def catchError(err):
    return "Internal error in server"


class BaseSurguardProtocol(LineReceiver):
    datarec = Signal()

    def __init__(self):
        self.state = "Empty"
        self.delimiter = MSG_END
        self.MAX_LENGTH = 128
        self.signals = WorkerSignals()
        self.signals.log_data.emit(f'A new connection is established')


    def connectionMade(self):
        self.sendLine(MSG_NAK)
        self._peer = self.transport.getPeer()
        logger.debug(f"Established new connection for {self._peer}")
        self.signals.log_data.emit(f"Established new connection for {self._peer}")
        self.state = "Client connected"
        self.call = reactor.callLater(60, self.send_ping)

    def connectionLost(self, reason):
        logger.debug(f"Connection lost {self._peer}")
        self.transport.loseConnection()
        self.state = "Client disconnected"
        self.sendLine(MSG_NAK)

    def lineReceived(self, line):
        self.signals.log_data.emit(f"Remote {self._peer} closed")
        d = self.factory.defer_msg(line, self._peer)
        d.addErrback(catchError)

        def writeResponse(message: bytes):
            if ConnectionState.connection_state == "Disconnected" or ConnectionState.reactor_running == False:
                self.transport.loseConnection()
            elif ConnectionState.connection_state == "Connected":
                self.transport.write(message)
                logger.info(f"Send answer to client {message}")

        d.addCallback(writeResponse)

    def send_ping(self):
        if self.state != "Client disconnected":
            self.transport.write(MSG_END)
            logger.info(f"send ping to {self._peer}")
            self.call = reactor.callLater(60, self.send_ping)


class SurguardFactory(protocol.ServerFactory):
    def __init__(self, signals):
        self.conn = ConnectToSql.conn
        self.buffer_in = BufferIn
        self.history = History
        self.signals = signals

    protocol = BaseSurguardProtocol

    def defer_msg(self, msg, ip):
        return defer.succeed(self.add_msg_to_db(msg, ip))

    def add_msg_to_db(self, msg, ip):
        current_time = int(datetime.now().timestamp())
        self.sg = SurGard(msg)
        ip = ip.host, ip.port
        if self.sg.is_valid():
            self.signals.log_data.emit('test')
            insert_to_buffer = insert(self.buffer_in).values(time=current_time, message=msg.decode()).compile()
            insert_to_history = insert(self.history).values(time=current_time, message=msg.decode(),
                                                            ip=str(ip)).compile()
            result = self.conn.execute(insert_to_history)
            result = self.conn.execute(insert_to_buffer)
            self.conn.commit()
            logger.info(f"inserting {msg}")
        else:
            logger.error(f'skip unknown message format {msg}')
        return MSG_ACK



class SurguardClientProtocol(LineReceiver):
    def __init__(self, peer_list):
        self._factory = SurguardClientFactory()
        self._peer = None
        self.peer_list = peer_list
        self.delimiter = MSG_END
        self.state = ""
        self.d = defer.Deferred()

    def connectionMade(self):
        self._peer = self.transport.getPeer()
        self.send_message()
        ConnectionState.connection_state = "Connected"
        logger.info(ConnectionState.connection_state)
        self.transport.setTcpKeepAlive(True)

    def dataReceived(self, data: bytes):
        logger.debug(f"Client receive {data}")

    def send_message(self):
        d = self.d
        if ConnectionState.connection_state == "Connected":

            row: tuple = self._factory.get_message_from_buffer()
            if row is not None:
                print(row.id, row.message)
                msg = row.message
                enc_msg = msg.encode()
                self.sendLine(enc_msg)
                logger.info(enc_msg)
                self._factory.remove_message_from_buffer(row.id)

            self.call = reactor.callLater(0.01, self.send_message)


class SurguardClientFactory(ReconnectingClientFactory):
    protocol: Optional[Callable[[], Protocol]] = SurguardClientProtocol

    def __init__(self):
        self.state = ''
        self.peer_list = []

    def startedConnecting(self, connector):
        logger.info("Started to connect.")

    def buildProtocol(self, addr: IAddress) -> "Optional[Protocol]":
        logger.info("Connected")
        logger.info("Resetting reconnection delay")
        ConnectionState.connection_state = "Connected"
        logger.info(ConnectionState.connection_state)
        self.resetDelay()
        return SurguardClientProtocol(self.peer_list)

    def clientConnectionLost(self, connector, unused_reason):
        logger.info("Lost connection.")
        ConnectionState.connection_state = "Disconnected"
        logger.info(ConnectionState.connection_state)
        ReconnectingClientFactory.clientConnectionLost(self, connector, unused_reason)

    def clientConnectionFailed(self, connector, reason):
        logger.info("Connection failed. Reason:", reason)
        ConnectionState.connection_state = "Disconnected"
        logger.info(ConnectionState.connection_state)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def update_state(self, message):
        self.state = message
        return self.state

    def defer_get_message_from_buffer(self):
        return defer.succeed(self.get_message_from_buffer)

    def get_message_from_buffer(self):
        row = ''
        statement = self.session.execute(select(self.buffer_in)).first()
        if statement is not None:
            for row in statement:
                logger.info(f"selecting {row.message}")
            return row

    def defer_remove_message_from_buffer(self, msg_id):
        return defer.succeed(self.remove_message_from_buffer(msg_id))

    def remove_message_from_buffer(self, msg_id):
        statement = delete(self.buffer_in).where(self.buffer_in.id == msg_id)
        self.conn.execute(statement)
        self.conn.commit()
        logger.info(f'deleting {msg_id}')


class ConnectionState:
    connection_state = ""
    reactor_running = True


class SurguardService(service.Service):
    def __init__(self):
        pass


class TwistedThread(QThread):
    def __init__(self):
        super().__init__()
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.signals = WorkerSignals()

    def run(self):
        logger.info('Worker data receiver start')
        surguard_endpoint = endpoints.serverFromString(reactor, f'tcp:{self.config["server"]["port"]}')
        surguard_endpoint.listen(SurguardFactory(self.signals))
        reactor.connectTCP(self.config["client"]["host"], self.config["client"]["port"], SurguardClientFactory())
        reactor.run(installSignalHandlers=0)
        ConnectionState.reactor_running = True

    def stop(self):
        ConnectionState.reactor_running = False
