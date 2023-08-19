import asyncio
import logging
from PySide6.QtCore import QThread


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MessageQueues:
    queue = asyncio.Queue()
    incoming_message_queues = asyncio.Queue(maxsize=100)
    outgoing_message_queues = asyncio.Queue()
    log_message_queues = asyncio.Queue()
    object_activity_queues = asyncio.Queue()
    
class WorkWithQueues:
    def __init__(self, signals) -> None:
        self.signals = signals
        self.message_queues = MessageQueues
    
    async def write_from_queue_to_log_window(self) -> None:
        while True:
            if self.message_queues.log_message_queues.empty():
                await asyncio.sleep(0.1)
            else:
                log_message = await self.message_queues.log_message_queues.get()
                self.signals.log_data.emit(log_message)
                await asyncio.sleep(0.001)
                # logger.info(f"message {log_message} get from buffer")
                
    async def write_from_queue_to_incoming_window(self) -> None:
        while True:
            if self.message_queues.incoming_message_queues.empty():
                await asyncio.sleep(1)
            else:

                ip, msg, event_msg = await self.message_queues.incoming_message_queues.get()
                self.signals.data_receive.emit(ip, msg, event_msg)
                await asyncio.sleep(0.01)


                # logger.info(f"message {ip}, {msg}, {event_msg} get from buffer")
                
    async def write_from_queue_to_outgoing_window(self) -> None:
        while True:
            if self.message_queues.outgoing_message_queues.empty():
                await asyncio.sleep(1)
            else:

                ip, msg, event_msg = await self.message_queues.outgoing_message_queues.get()
                self.signals.data_send.emit(ip, msg, event_msg)
                await asyncio.sleep(0.01)

                # logger.info(f"message {ip}, {msg}, {event_msg}  get from buffer")

    async def write_from_queue_to_object_activity_window(self) -> None:
        while True:
            if self.message_queues.object_activity_queues.empty():
                await asyncio.sleep(1)
            else:

                object_number, timestamp = await self.message_queues.object_activity_queues.get()
                self.signals.objects_activity.emit(object_number, timestamp)
                await asyncio.sleep(0.01)
                # logger.info(f"message {ip}, {msg}, {event_msg}  get from buffer")

                
class MessageQueueThread(QThread):
    def __init__(self, signals) -> None:
        super().__init__()
        self.signals = signals
        self.message_queues = MessageQueues
        self.work_with_queues = WorkWithQueues(self.signals)
        self.tasks = []
        self.loop = asyncio.new_event_loop()
        
    def run(self) -> None:
        self.signals.log_data.emit("Worker data queue start")
        try:
            logger.info("Worker data queue start")
            self.loop.run_until_complete(self.setup_tasks())
        except KeyboardInterrupt:
            print("Server and client stopped by user")
            self.signals.log_data.emit("Server and client stopped by user")

    def stop(self):
        self.loop.call_soon_threadsafe(self._stop)

    def _stop(self):
        for task in self.tasks:
            task.cancel()

    async def setup_tasks(self):
        self.tasks.append(asyncio.create_task(self.work_with_queues.write_from_queue_to_incoming_window()))
        self.tasks.append(asyncio.create_task(self.work_with_queues.write_from_queue_to_outgoing_window()))
        self.tasks.append(asyncio.create_task(self.work_with_queues.write_from_queue_to_log_window()))
        self.tasks.append((asyncio.create_task(self.work_with_queues.write_from_queue_to_object_activity_window())))
        self.group = asyncio.gather(*self.tasks, return_exceptions=True)

        try:
            await self.group
        except asyncio.CancelledError:
            print("Tasks cancelled")
