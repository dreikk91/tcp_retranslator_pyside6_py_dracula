import asyncio
import logging

from net.retranslator_asyncio.server.check_connection import ConnectionState
from net.retranslator_asyncio.server.client_hendler import ClientHandler

logger = logging.getLogger(__name__)


class KeepAliveTimer(ClientHandler):
    def __init__(self):
        super(KeepAliveTimer, self).__init__()

    async def keepalive(self) -> None:
        # Відправка пакетів підтримки з'єднання
        while True:
            if ConnectionState.is_running.is_set():
                for writer in self.clients.copy():
                    try:
                        # await asyncio.sleep(10)
                        if not writer.is_closing() or not writer:
                            writer.write(b"\x01")
                            await writer.drain()
                            logger.info(
                                f"send keep-alive to {writer.get_extra_info('peername')}"
                            )
                            # self.signals.log_data.emit(
                            #     f"send keep-alive to {client.get_extra_info('peername')}"
                            # )
                            await self.message_queues.log_message_queues.put(
                                f"send keep-alive to {writer.get_extra_info('peername')}"
                            )

                    except (
                        ConnectionResetError,
                        ConnectionError,
                        OSError,
                        asyncio.IncompleteReadError,
                    ) as err:
                        await self._handle_error(writer, err)
                        logger.error(f"Keepalive failed {err}")

            await asyncio.sleep(self.keepalive_interval)
