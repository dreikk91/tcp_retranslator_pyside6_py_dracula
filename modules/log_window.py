from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from datetime import datetime

from common.yaml_config import YamlConfig


class LogWindow:
    def __init__(self, widgets) -> None:
        self.widgets = widgets
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.log_window = self.widgets.listWidget_log

    @Slot(str)
    def fill_log_window(self, message):
        time_now = datetime.now().strftime("%d/%m/%Y | %H:%M:%S.%f")
        msg = QListWidgetItem(f"{time_now} | {message}")
        if self.log_window.count() >= self.config["other"]["log_window_row_count"]:
            self.log_window.takeItem(0)
        self.log_window.addItem(msg)
        self.log_window.setUniformItemSizes(True)
        if not self.log_window.hasFocus():
            self.log_window.scrollToBottom()
