import asyncio
import json
import logging

from common.message_queues import MessageQueues
from common.read_events_name_from_json import get_event_from_json
from database.sql_part_sync import (
    check_connection,
    create_engine_and_session,
    select_from_buffer_sync,
    delete_from_buffer_sync,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MSG_END: bytes = b"\x14"
MSG_ACK: bytes = b"\x06"
MSG_NAK: bytes = b"\x15"

SESSION_FILE = "session.json"


class EventForwarder:
    def __init__(self, server_host: str, server_port: int, signals) -> None:
        self._server_host: str = server_host
        self._server_port: int = server_port
        self._signals = signals
        self._retry_count: int = 0
        self._writer = None
        self._reader = None
        self._engine, self._session = create_engine_and_session()
        self._message_queues = MessageQueues()
        self._outgoing_msg = ()
        self._stop_event = asyncio.Event()

    async def establish_connection(self, timeout: int = 3) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._server_host, self._server_port),
                timeout=timeout,
            )
            logger.info(f"Connected to {self._server_host}:{self._server_port}")
            await self._log_and_put_message(f"Connected to {self._server_host}:{self._server_port}")
        except asyncio.TimeoutError as ex:
            await self._handle_connection_error(f"Connection to {self._server_host}:{self._server_port} timed out", ex)
        except OSError as ex:
            await self._handle_connection_error(f"Error connecting to {self._server_host}:{self._server_port}: {ex}", ex)

    async def _handle_connection_error(self, message: str, exception: Exception) -> None:
        logger.error(message)
        await self._log_and_put_message(message)
        raise ConnectionError(message) from exception

    async def send_data_to_server(self, data: bytes) -> bool:
        try:
            if self._writer:
                self._writer.write(data)
                await self._writer.drain()
                response = await asyncio.wait_for(self._reader.read(1024), timeout=5)

                logger.info(f"Sent data: {data}, Received response: {response}")
                # await self._log_and_put_message(f"Sent data: {data}, Received response: {response}")

                decoded_data = data.decode()
                event_code = f"{decoded_data[11]}{decoded_data[12:15]}"
                event_message = get_event_from_json.read_events(event_code)
                self._outgoing_msg = (
                    self._writer.get_extra_info("peername"),
                    data.decode(),
                    event_message,
                )
                await self._message_queues.outgoing_message_queues.put(self._outgoing_msg)

                return True

        except (ConnectionResetError, TimeoutError, OSError) as e:
            await self._handle_send_data_error(f"Error sending data: {e}")

        except AttributeError:
            await self._handle_send_data_error("Got None in self._writer.write(data)")

        except RuntimeError as err:
            await self._handle_send_data_error(str(err))

        return False

    async def _handle_send_data_error(self, message: str) -> None:
        logger.error(message)
        await self._log_and_put_message(message)

    async def _log_and_put_message(self, message: str) -> None:
        await self._message_queues.log_message_queues.put(message)
        logger.info(message)

    async def retry_connection_with_backoff(self, max_retries: int = 99, base_delay: int = 2) -> None:
        retries = 0
        while retries < max_retries:
            try:
                await self._ensure_connection()
                return
            except ConnectionError as e:
                delay = min(2 ** retries * base_delay, 60)
                retries += 1
                logger.info(f"Retrying in {delay} seconds... (Retry {retries}/{max_retries})")
                await self._log_and_put_message(f"Retrying in {delay} seconds... (Retry {retries}/{max_retries})")
                await asyncio.sleep(delay)

        logger.error(f"Max retries reached. Unable to establish connection.")
        await self._log_and_put_message(f"Max retries reached. Unable to establish connection.")
        # Handle max retries reached scenario (e.g., raise an exception or perform cleanup)

    async def _ensure_connection(self) -> None:
        if self._writer is None or self._writer.is_closing():
            logger.info(
                f"Connecting to the SurGard server to forward events...{self._server_host}:{self._server_port}"
            )
            await self._log_and_put_message(
                f"Connecting to the SurGard server to forward events...{self._server_host}:{self._server_port}"
            )
            await self.establish_connection()
        else:
            await asyncio.sleep(0.1)

    async def start_tcp_client(self) -> None:
        asyncio.create_task(self._start_tasks())
        await self._stop_event.wait()

    async def _start_tasks(self):
        while not self._stop_event.is_set():
            try:
                await asyncio.gather(
                    self.retry_connection_with_backoff(),
                    self.send_messages_from_buffer(),

                )
                await self._wait_with_timeout()
            except Exception as e:
                await self._handle_error(e)

    async def _wait_with_timeout(self, timeout: int = 0.1) -> None:
        await asyncio.sleep(timeout)

    async def send_messages_from_buffer(self) -> None:
        if check_connection(self._engine):
            rows = select_from_buffer_sync(self._session)
            if rows is not None:
                for row in rows:
                    row_id: int = row[0]
                    message: str = row[1]

                    success = await self.send_data_to_server(message.encode())
                    if success:
                        delete_from_buffer_sync(self._session, row_id)
                        logger.debug(f"Delete from buffer by id {row_id}")
                        # await self._log_and_put_message(f"Delete from buffer by id {row_id}")
                    else:
                        logger.error(f"{message} not sent")

                        await self._log_and_put_message(f"{message} not sent")
                        await asyncio.sleep(1)
            else:
                await asyncio.sleep(0)
        else:
            logger.error("Connection to database not exist")
            await self._log_and_put_message("Connection to database not exist")
            await asyncio.sleep(10)
            self._engine, self._session = create_engine_and_session()

    async def _handle_error(self, e) -> None:
        logger.error(f"Error in run method: {e}")
        await self._log_and_put_message(f"Error in run method: {e}")
        # delay = 2 ** (self._retry_count if self._retry_count < 7 else 7)
        self._retry_count += 1
        # logger.error(f"Retrying in {delay} seconds...")
        # await self._log_and_put_message(f"Retrying in {delay} seconds...")
        # await asyncio.sleep(delay)

    def save_session(self) -> None:
        # Збереження параметрів сесії в файл
        session_data = {
            "server_host": self._server_host,
            "server_port": self._server_port,
            "retry_count": self._retry_count,
        }
        with open(SESSION_FILE, "w") as file:
            json.dump(session_data, file)

    def load_session(self) -> None:
        # Відновлення параметрів сесії з файлу
        try:
            with open(SESSION_FILE, "r") as file:
                session_data = json.load(file)
                self._server_host = session_data["server_host"]
                self._server_port = session_data["server_port"]
                self._retry_count = session_data["retry_count"]
        except FileNotFoundError:
            pass  # Файл сесії не знайдено, продовжити зі значеннями за замовчуванням
