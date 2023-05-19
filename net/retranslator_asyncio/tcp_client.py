import asyncio
import logging

from common.read_events_name_from_json import get_event_from_json
# from common.logger_config import logger
from common.sql_part import select_from_buffer_sync, delete_from_buffer_sync

logger = logging.getLogger(__name__)


class TCPClient:
    def __init__(self, server_host, server_port, signals):
        self.writer = None
        self.reader = None
        self.retry_count: int = 0
        self.server_host: str = server_host
        self.server_port: int = server_port
        self.signals = signals

    async def establish_connection(self, timeout=3):
        """Підключення до сервера з можливістю встановлення таймауту"""
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.server_host, self.server_port),
                timeout=timeout,
            )
            logger.info(f"Connected to {self.server_host}:{self.server_port}")
            self.signals.log_data.emit(
                f"Connected to {self.server_host}:{self.server_port}"
            )

        except asyncio.TimeoutError as ex:
            raise ConnectionError(
                f"Connection to {self.server_host}:{self.server_port} timed out"
            ) from ex
        except OSError as e:
            logger.exception(f"Error connecting to server:")
            self.signals.log_data.emit(f"Error connecting to server: {e}")
            raise ConnectionError(
                f"Error connecting to {self.server_host}:{self.server_port}: {e}"
            ) from e

    async def send_data_to_server(self, data):
        """Відправлення повідомлення"""
        try:
            self.writer.write(data)
            await self.writer.drain()

            response = await asyncio.wait_for(self.reader.read(1024), timeout=0.1)

            # if response == MSG_ACK:
            logger.info(f"Sent data: {data}, Received response: {response}")
            self.signals.log_data.emit(
                f"Sent data: {data}, Received response: {response}"
            )
            decoded_data = data.decode()
            # event_type = decoded_data[11]
            # event_code = decoded_data[12:15]
            event_code = f'{decoded_data[11]}{decoded_data[12:15]}'
            # allcodes = [*event_guard, *event_disguard, *event_alarm, *event_ok, *other_events]
            # for i in range(1000000):
            #     for code in allcodes:
            #         event_code = code
            #         event_message = get_event_from_json.read_events(event_code)
            #         self.signals.data_send.emit(
            #             self.writer.get_extra_info("peername"), data.decode(), event_message
            #         )
            #         await asyncio.sleep(0.01)
            #         self.signals.log_data.emit("Message not accepted? try again")
            #
            #     i+=1
            event_message = get_event_from_json.read_events(event_code)
            self.signals.data_send.emit(
                self.writer.get_extra_info("peername"), data.decode(), event_message
            )


            # else:
            #     # await asyncio.sleep(1)
            #     # await insert_into_buffer(data.decode())
            #     logger.error("Message not accepted")
            #     self.signals.log_data.emit("Message not accepted? try again")

        except ConnectionResetError as e:
            logger.exception(f"Error sending data:")
            self.signals.log_data.emit(f"Error sending data: {e}")

        except TimeoutError as e:
            logger.exception(f"Error sending data:")
            self.signals.log_data.emit(f"Error sending data: {e}")

        except OSError as e:
            logger.exception(f"Error sending data:")
            self.signals.log_data.emit(f"Error sending data: {e}")

        except AttributeError:
            logger.exception('Got None in self.writer.write(data)')

        except RuntimeError as err:
            logger.exception(err)

    async def start_tcp_client(self):
        """Основна функція"""
        while True:
            try:
                await asyncio.sleep(0.01)
                # Підключення до сервера
                await self.ensure_connection()
                # await asyncio.sleep(0.01)
                # Відправлення повідомлення
                await self.send_messages_from_buffer()

            except OSError as e:
                await self.handle_error(e)

    async def ensure_connection(self):
        if self.writer is None or self.writer.is_closing():
            logger.info(f"Connecting to the SurGard server to"
                        f" forward events...{self.server_host}:{self.server_port}")
            self.signals.log_data.emit(f"Connecting to the SurGard server"
                                       f" to forward events ...{self.server_host}:{self.server_port}")
            try:
                await self.establish_connection()
            except ConnectionError as e:
                logger.exception(f"Error connecting to server:")
                self.signals.log_data.emit(f"Error connecting to server: {e}")
                delay = min(2 ** self.retry_count, 60)  # Exponential backoff with a max delay of 60 seconds
                self.retry_count += 1
                logger.info(f"Retrying in {delay} seconds...")
                self.signals.log_data.emit(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                # raise
        else:
            await asyncio.sleep(0.1)

    async def send_messages_from_buffer(self):
        row_id = 0
        message = 0
        # row = await select_from_buffer()
        rows = select_from_buffer_sync()
        if rows is not None:
            for row in rows:
                row_id = row[0]
                message = row[1]
                # await asyncio.sleep(0.01)
                await self.send_data_to_server(message.encode())
                # await asyncio.sleep(0.01)
                delete_from_buffer_sync(row_id)
                # await delete_from_buffer(row.id)
                logger.debug(f"Delete from buffer by id {row_id}")
                self.signals.log_data.emit(f"Delete from buffer by id {row_id}")
        else:
            await asyncio.sleep(0.01)

    async def handle_error(self, e):
        logger.error(f"Error in run method: {e}")
        self.signals.log_data.emit(f"Error in run method: {e}")
        delay = 2 ** (self.retry_count if self.retry_count < 7 else 7)
        self.retry_count += 1
        logger.info(f"Retrying in {delay} seconds...")
        self.signals.log_data.emit(f"Retrying in {delay} seconds...")
        await asyncio.sleep(delay)
