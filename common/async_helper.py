import asyncio
from PySide6.QtCore import QEvent, QObject, Signal, Slot
from PySide6.QtWidgets import QApplication


class AsyncHelper(QObject):
    class ReenterQtObject(QObject):
        """This is a QObject to which an event will be posted, allowing
        asyncio to resume when the event is handled. event.fn() is
        the next entry point of the asyncio event loop."""

        def event(self, event):
            if event.type() == QEvent.Type.User + 1:
                event.fn()
                return True
            return False

    class ReenterQtEvent(QEvent):
        """This is the QEvent that will be handled by the ReenterQtObject.
        self.fn is the next entry point of the asyncio event loop."""

        def __init__(self, fn):
            super().__init__(QEvent.Type(QEvent.Type.User + 1))
            self.fn = fn

    def __init__(self, worker, entry):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = entry
        self.loop = asyncio.new_event_loop()
        self.done = False

        self.worker = worker
        print(dir(worker))
        print(hasattr(self.worker, "start_signal"))
        if hasattr(self.worker, "start_signal") and isinstance(
            self.worker.start_signal, Signal
        ):
            self.worker.start_signal.connect(self.on_worker_started)
        if hasattr(self.worker, "done_signal") and isinstance(
            self.worker.done_signal, Signal
        ):
            self.worker.done_signal.connect(self.on_worker_done)

    @Slot()
    def on_worker_started(self):
        """To use asyncio and Qt together, one must run the asyncio
        event loop as a "guest" inside the Qt "host" event loop."""
        if not self.entry:
            raise Exception("No entry point for the asyncio event loop was set.")
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.entry())
        self.loop.call_soon(self.next_guest_run_schedule)
        self.done = (
            False  # Set this explicitly as we might want to restart the guest run.
        )
        self.loop.run_forever()

    @Slot()
    def on_worker_done(self):
        """When all our current asyncio tasks are finished, we must end
        the "guest run" lest we enter a quasi idle loop of switching
        back and forth between the asyncio and Qt loops. We can
        launch a new guest run by calling launch_guest_run() again."""
        self.done = True

    def continue_loop(self):
        """This function is called by an event posted to the Qt event
        loop to continue the asyncio event loop."""
        if not self.done:
            self.loop.call_soon(self.next_guest_run_schedule)
            self.loop.run_forever()

    def next_guest_run_schedule(self):
        """This function serves to pause and re-schedule the guest
        (asyncio) event loop inside the host (Qt) event loop. It is
        registered in asyncio as a callback to be called at the next
        iteration of the event loop. When this function runs, it
        first stops the asyncio event loop, then by posting an event
        on the Qt event loop, it both relinquishes to Qt's event
        loop and also schedules the asyncio event loop to run again.
        Upon handling this event, a function will be called that
        resumes the asyncio event loop."""
        self.loop.stop()
        QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(self.continue_loop))
