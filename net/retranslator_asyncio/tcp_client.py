import asyncio

from common.logger_config import logger
from common.sql_part import select_from_buffer, delete_from_buffer
from common.read_events_name_from_json import *

class TCPClient:
    def __init__(self, server_host, server_port, signals):
        self.writer = None
        self.reader = None
        self.retry_count = None
        self.server_host = server_host
        self.server_port = server_port
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

        except asyncio.TimeoutError:
            raise ConnectionError(
                f"Connection to {self.server_host}:{self.server_port} timed out"
            )
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            self.signals.log_data.emit(f"Error connecting to server: {e}")
            raise ConnectionError(
                f"Error connecting to {self.server_host}:{self.server_port}: {e}"
            )


    async def send_data_to_server(self, data):
        """Відправлення повідомлення"""
        try:
            self.writer.write(data)
            await self.writer.drain()

            response = await asyncio.wait_for(self.reader.read(1024), timeout=10)
            # if response == MSG_ACK:
            logger.info(f"Sent data: {data}, Received response: {response}")
            self.signals.log_data.emit(
                f"Sent data: {data}, Received response: {response}"
            )
            decoded_data = data.decode()
            event_type = decoded_data[11]
            event_code = decoded_data[12:15]
            event_message = await read_json.find_event_name_by_type_and_code(events, dictionary_add, event_type,
                                                                       int(event_code))
            self.signals.data_send.emit(
                self.writer.get_extra_info("peername"), data.decode(), event_message
            )

            # else:
            #     # await asyncio.sleep(1)
            #     # await insert_into_buffer(data.decode())
            #     logger.error("Message not accepted")
            #     self.signals.log_data.emit("Message not accepted? try again")

            return True
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            self.signals.log_data.emit(f"Error sending data: {e}")
            return False

    async def start_tcp_client(self):
        """Основна функція"""
        while True:
            try:
                # Підключення до сервера
                await self.ensure_connection()

                # Відправлення повідомлення
                await self.send_messages_from_buffer()
                await asyncio.sleep(0.001)

            except Exception as e:
                await self.handle_error(e)

    async def ensure_connection(self):
        if self.writer is None or self.writer.is_closing():
            logger.info("Connecting to server...")
            self.signals.log_data.emit("Connecting to server...")
            try:
                await self.establish_connection()
            except Exception as e:
                logger.error(f"Error connecting to server: {e}")
                self.signals.log_data.emit(f"Error connecting to server: {e}")
                delay = min(2 ** self.retry_count, 60)  # Exponential backoff with a max delay of 60 seconds
                self.retry_count += 1
                logger.info(f"Retrying in {delay} seconds...")
                self.signals.log_data.emit(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                # raise

    async def send_messages_from_buffer(self):
        row = await select_from_buffer()
        if row is not None:
            await self.send_data_to_server(row.message.encode())
            await delete_from_buffer(row.id)
            logger.debug(f"Delete from buffer by id {row.id}")
            self.signals.log_data.emit(f"Delete from buffer by id {row.id}")
        else:
            await asyncio.sleep(0.1)

    async def handle_error(self, e):
        logger.error(f"Error in run method: {e}")
        self.signals.log_data.emit(f"Error in run method: {e}")
        delay = 2 ** (self.retry_count if self.retry_count < 7 else 7)
        self.retry_count += 1
        logger.info(f"Retrying in {delay} seconds...")
        self.signals.log_data.emit(f"Retrying in {delay} seconds...")
        await asyncio.sleep(delay)
