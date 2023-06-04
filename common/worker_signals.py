import logging

from PySide6.QtCore import QObject, Signal

from common.logger_config import logger

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    '''

    data_receive = Signal(tuple, str, dict)
    data_send = Signal(tuple, str, dict)
    log_data = Signal(str)
    
    start_signal = Signal()
    start_client_signal = Signal()
    stop_server_signal = Signal()
    stop_client_signal = Signal()

    stop_signal = Signal()

    group_info = Signal(str, str, str, str, str, str, str)
    pipline_info = Signal(str, str, str, str, str)
    progressBarValue = Signal(int, int)

    main_info = Signal(str, str, str, str, str, str, str, str, str, str, str)

    journal = Signal(str, str, str, str, str, str, int, int)
