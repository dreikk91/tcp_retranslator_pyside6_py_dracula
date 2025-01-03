import asyncio
from asyncio import Event


class ConnectionState:
    # Клас, що відстежує стан підключення серверу
    is_running: Event = asyncio.Event()
    server_is_running = True
    ready_for_closed = False

    async def _check_connection_state(self) -> None:
        # Check the connection state
        if not ConnectionState.is_running.is_set():
            raise ConnectionError("Server is not running")
