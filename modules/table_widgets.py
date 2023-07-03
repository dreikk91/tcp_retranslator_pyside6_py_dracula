import time
from datetime import datetime
from common.worker_signals import WorkerSignals
from PySide6 import QtWidgets

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from common.surguad_codes import get_color_by_event
from common.yaml_config import YamlConfig
# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
import logging

logger = logging.getLogger(__name__)

class TableManager:
    def __init__(self, widgets) -> None:
        self.widgets = widgets
        self.signals = WorkerSignals()
        
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.left_table_widget = self.widgets.tableWidget_left
        self.right_table_widget = self.widgets.tableWidget_right_2
        self.objects_table_widget = self.widgets.tableWidget_objects
        
        self.left_row_counter = 0
        self.right_row_counter = 0

        self.message_received_count = 0
        self.message_sent_count = 0
        
        self.message_received_count = 0
        self.message_received_count_per_second = 0
        self.message_send_count_per_second = 0
        self.send_messages_per_second = 0
        self.received_messages_per_second = 0
        self.start_time_send = time.time()
        self.start_time_receive = time.time()
        
        self.object_list = []


    def customize_left_table_widgets(self):
        self.left_table_widget.autoScrollMargin()
        for i in range(8):
            self.left_table_widget.resizeColumnToContents(i)

    def customize_right_table_widgets(self):
        self.right_table_widget.autoScrollMargin()
        for i in range(8):
            self.right_table_widget.resizeColumnToContents(i)

    @Slot(tuple, dict)
    def add_row_to_incoming_widget(self, peer_name, message, event_message):
        current_time: str = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        ppk_id: str = message[7:11]
        line: str = message[3]
        event_type: str = message[11]
        event_code: str = message[12:15]
        group: str = message[15:17]
        zone: str = message[17:20]
        background_color, forground_color = get_color_by_event(
            event_message["contactId_code"]
        )
        event_text: str = f'{event_message["CodeMes_UK"]} ({event_type}{event_code})'

        if self.left_row_counter <= 10:
            self.customize_left_table_widgets()

        if (
                self.left_table_widget.rowCount()
                >= self.config["other"]["left_window_row_count"]
        ):
            self.left_table_widget.removeRow(0)
        row = self.left_table_widget.rowCount()
        self.left_table_widget.insertRow(row)
        items = [
            QTableWidgetItem(current_time),
            QTableWidgetItem(ppk_id),
            QTableWidgetItem(line),
            QTableWidgetItem(f'{event_message["TypeCodeMes_UK"]}'),
            QTableWidgetItem(event_text),
            QTableWidgetItem(group),
            QTableWidgetItem(zone),
            QTableWidgetItem(f"{peer_name[0]}:{peer_name[1]}"),
        ]

        for i, item in enumerate(items):
            item.setBackground(QColor(background_color))
            item.setForeground(QColor(forground_color))
            self.left_table_widget.setItem(row, i, item)
        if not self.left_table_widget.hasFocus():
            self.left_table_widget.scrollToItem(
                items[0], QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible
            )
        else:
            self.left_table_widget.setAutoScroll(False)
        self.left_row_counter += 1
        self.message_received_count += 1
        self.message_received_count_per_second += 1
        elapsed_time = time.time() - self.start_time_receive
        if elapsed_time >= 1:
            self.received_messages_per_second = self.message_received_count_per_second / elapsed_time
            self.start_time_receive = time.time()
            self.message_received_count_per_second = 0
            # print(f"Messages per second: {round(self.received_messages_per_second, 2)}")
        self.update_receive_send_count()
        # self.ui.label_message_receviced_count.setText(str(self.message_received_count))

    @Slot(tuple, str)
    def add_row_to_outgoing_widget(self, peer_name, message, event_message):
        event_message = event_message
        current_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        ppk_id = message[7:11]
        line = message[3]
        event_type = message[11]
        event_code = message[12:15]
        group = message[15:17]
        zone = message[17:20]
        background_color, forground_color = get_color_by_event(
            event_message["contactId_code"]
        )
        event_text = f'{event_message["CodeMes_UK"]} ({event_type}{event_code})'

        if self.right_table_widget.rowCount() <= 10:
            self.customize_right_table_widgets()

        if (
                self.right_table_widget.rowCount()
                >= self.config["other"]["right_window_row_count"]
        ):
            self.right_table_widget.removeRow(0)

        row = self.right_table_widget.rowCount()
        self.right_table_widget.insertRow(row)
        items = [
            QTableWidgetItem(current_time),
            QTableWidgetItem(ppk_id),
            QTableWidgetItem(line),
            QTableWidgetItem(f'{event_message["TypeCodeMes_UK"]}'),
            QTableWidgetItem(event_text),
            QTableWidgetItem(group),
            QTableWidgetItem(zone),
            QTableWidgetItem(f"{peer_name[0]}:{peer_name[1]}"),
        ]

        for i, item in enumerate(items):
            self.right_table_widget.setItem(row, i, item)
            item.setBackground(QColor(background_color))
            item.setForeground(QColor(forground_color))
        if not self.right_table_widget.hasFocus():
            self.right_table_widget.scrollToItem(
                items[0], QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible
            )
        self.right_row_counter += 1
        self.message_sent_count += 1
        self.message_send_count_per_second += 1
        elapsed_time = time.time() - self.start_time_send
        if elapsed_time >= 1:
            self.send_messages_per_second = self.message_send_count_per_second / elapsed_time
            self.start_time_send = time.time()
            self.message_send_count_per_second = 0
            # print(f"Messages per second: {round(self.send_messages_per_second, 2)}")
        self.update_receive_send_count()
        
    def update_receive_send_count(self):
        self.widgets.label_receive_send_count.setText(
            f"Total Receive/Send: {self.message_received_count} / {self.message_sent_count}"
                    )
        self.widgets.label_receive_send_speed.setText(
            f"Recieve/Send speed: {round(self.received_messages_per_second, 2)} / {round(self.send_messages_per_second, 2)}"
        )
    
    @Slot(str, str) 
    def add_row_to_objects_table(self, data, timestamp):
        # data = data
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        
        if data not in self.object_list:
            row_count = self.objects_table_widget.rowCount()
            self.objects_table_widget.insertRow(row_count)
            self.objects_table_widget.setItem(row_count, 0, QTableWidgetItem(data))
            self.objects_table_widget.setItem(row_count, 5, QTableWidgetItem(timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")))
            self.objects_table_widget.setItem(row_count, 3, QTableWidgetItem(''))
            self.object_list.append(data)
        else:
            for row in range(self.objects_table_widget.rowCount()):
                
                if self.objects_table_widget.item(row, 0).text() == data:
                    try:
                        timedelta = timestamp - datetime.strptime(self.objects_table_widget.item(row, 5).text(), "%Y-%m-%d %H:%M:%S.%f")
                    except AttributeError as err:
                        logger.exception()
                        timedelta = ''
                    self.objects_table_widget.item(row, 5).setText(str(timestamp))
                    
                    self.objects_table_widget.item(row, 3).setText(str(timedelta))
                    break
            
        if self.objects_table_widget.rowCount() <=10:
            self.objects_table_widget.resizeColumnToContents(3)
            self.objects_table_widget.resizeColumnToContents(5)

                