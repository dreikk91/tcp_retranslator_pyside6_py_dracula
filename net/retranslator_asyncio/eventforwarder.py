import asyncio
import logging

from common.read_events_name_from_json import get_event_from_json
from database.sql_part_postgres_sync import select_from_buffer_sync, delete_from_buffer_sync
# from database.sql_part_sqlite import select_from_buffer_sync, delete_from_buffer_sync

logger = logging.getLogger(__name__)


class EventForwarder:
    def __init__(self, server_host: str, server_port: int, signals) -> None:
        self.server_host: str = server_host
        self.server_port: int = server_port
        self.signals = signals
        self.retry_count: int = 0
        self.writer = None
        self.reader = None

    async def establish_connection(self, timeout: int = 3) -> None:
        try:
            # Establish a TCP connection with the server
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.server_host, self.server_port),
                timeout=timeout,
            )
            logger.info(f"Connected to {self.server_host}:{self.server_port}")
            self.signals.log_data.emit(f"Connected to {self.server_host}:{self.server_port}")
        except asyncio.TimeoutError as ex:
            # Handle timeout error
            raise ConnectionError(f"Connection to {self.server_host}:{self.server_port} timed out") from ex
        except OSError as e:
            # Handle general OS-related errors
            logger.exception(f"Error connecting to server:")
            self.signals.log_data.emit(f"Error connecting to server: {e}")
            raise ConnectionError(f"Error connecting to {self.server_host}:{self.server_port}: {e}") from e

    async def send_data_to_server(self, data: bytes) -> None:
        if self.writer is None:
            logger.error("Не вдалося підключитися до сервера. Операція неможлива.")
            return False
        
        try:
            # Send data to the server and receive the response
            self.writer.write(data)
            await self.writer.drain()
            response = await asyncio.wait_for(self.reader.read(1024), timeout=1)

            logger.info(f"Sent data: {data}, Received response: {response}")
            self.signals.log_data.emit(f"Sent data: {data}, Received response: {response}")

            # Decode the data and extract event information
            decoded_data = data.decode()
            event_code = f'{decoded_data[11]}{decoded_data[12:15]}'
            event_message = get_event_from_json.read_events(event_code)
            self.signals.data_send.emit(
                self.writer.get_extra_info("peername"), data.decode(), event_message
            )
            return True
        except (ConnectionResetError, TimeoutError, OSError) as e:
            # Handle connection-related errors
            logger.exception(f"Error sending data:")
            self.signals.log_data.emit(f"Error sending data: {e}")
        except AttributeError:
            # Handle attribute error related to writer.write()
            logger.exception('Got None in self.writer.write(data)')
            self.writer.close()
        except RuntimeError as err:
            # Handle general runtime errors
            logger.exception(err)
            
        return False

    async def start_tcp_client(self) -> None:
        while True:
            try:
                await self.ensure_connection()
                await self.send_messages_from_buffer()
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.exception(e)
                # Handle OS-related errors during the client execution
                await self.handle_error(e)

    async def ensure_connection(self) -> None:
        if self.writer is None or self.writer.is_closing():
            # Check if a connection needs to be established or re-established
            logger.info(f"Connecting to the SurGard server to forward events...{self.server_host}:{self.server_port}")
            self.signals.log_data.emit(f"Connecting to the SurGard server to forward events...{self.server_host}:{self.server_port}")
            try:
                await self.establish_connection()
            except ConnectionError as e:
                # Handle connection errors and retry with exponential backoff
                logger.exception(f"Error connecting to server:")
                self.signals.log_data.emit(f"Error connecting to server: {e}")
                delay = min(2 ** self.retry_count, 60)
                self.retry_count += 1
                logger.info(f"Retrying in {delay} seconds...")
                self.signals.log_data.emit(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        else:
            await asyncio.sleep(0.1)

    async def send_messages_from_buffer(self) -> None:
        rows = select_from_buffer_sync()
        if rows is not None:
            for row in rows:
                row_id: int = row[0]
                message: str = row[1]
                # Send each message from the buffer to the server
                success = await self.send_data_to_server(message.encode())
                if success:
                    # Delete the sent message from the buffer
                    delete_from_buffer_sync(row_id)
                    logger.debug(f"Delete from buffer by id {row_id}")
                    self.signals.log_data.emit(f"Delete from buffer by id {row_id}")
                else:
                    logger.info(f"{message} not sended")
        else:
            await asyncio.sleep(0.01)

    async def handle_error(self, e) -> None:
        # Handle errors that occur during the client execution
        logger.error(f"Error in run method: {e}")
        self.signals.log_data.emit(f"Error in run method: {e}")
        delay = 2 ** (self.retry_count if self.retry_count < 7 else 7)
        self.retry_count += 1
        logger.info(f"Retrying in {delay} seconds...")
        self.signals.log_data.emit(f"Retrying in {delay} seconds...")
        await asyncio.sleep(delay)
