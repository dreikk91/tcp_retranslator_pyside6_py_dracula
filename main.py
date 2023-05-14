# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

import sys
import os
import platform

from PySide6.QtGui import QColor


# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
from net.retranslator_asyncio.runner import RetranslatorThread
from net.retranslator_asyncio.tcp_server import ConnectionState
from common.read_events_name_from_json import *
from common.surguad_codes import get_color_by_event
from widgets import *

os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        self.signals = WorkerSignals()

        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()

        self.left_table_widget = widgets.tableWidget_left
        self.right_table_widget = widgets.tableWidget_right_2
        self.log_window = widgets.listWidget_log

        self.left_row_counter = 0
        self.right_row_counter = 0

        self.tcp_client = TcpClient(self.signals)
        self.tcp_server = MyTcpServer(self.signals)

        self.message_received_count = 0
        self.message_sent_count = 0
        #
        # self.start_tcp_client_thread()
        # self.start_tcp_server_thread()
        ConnectionState.is_running.set()
        self.retranslator = RetranslatorThread(self.signals)
        self.start_retranslator_async_thread()

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "TCP Surgurad Retranslator"
        description = "TCP Surgurad Retranslator APP"
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # QTableWidget PARAMETERS
        # ///////////////////////////////////////////////////////////////
        # widgets.tableWidget_left.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # widgets.tableWidget_right_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        widgets.btn_home.clicked.connect(self.buttonClick)
        widgets.btn_log.clicked.connect(self.buttonClick)
        # widgets.btn_new.clicked.connect(self.buttonClick)
        # widgets.btn_save.clicked.connect(self.buttonClick)

        # EXTRA LEFT BOX
        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)

        widgets.toggleLeftBox.clicked.connect(openCloseLeftBox)
        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        # EXTRA RIGHT BOX
        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)

        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = True
        themeFile = "themes\\py_dracula_light.qss"

        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        widgets.stackedWidget.setCurrentWidget(widgets.widget_retranslator)
        widgets.btn_home.setStyleSheet(
            UIFunctions.selectMenu(widgets.btn_home.styleSheet())
        )

    # BUTTONS CLICK
    # Post here your functions for clicked buttons
    # ///////////////////////////////////////////////////////////////
    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            widgets.stackedWidget.setCurrentWidget(widgets.widget_retranslator)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW WIDGETS PAGE
        if btnName == "btn_log":
            widgets.stackedWidget.setCurrentWidget(widgets.widget_log)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # # SHOW NEW PAGE
        # if btnName == "btn_new":
        #     widgets.stackedWidget.setCurrentWidget(widgets.new_page) # SET PAGE
        #     UIFunctions.resetStyle(self, btnName) # RESET ANOTHERS BUTTONS SELECTED
        #     btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) # SELECT MENU

        # if btnName == "btn_save":
        #     print("Save BTN clicked!")

        # PRINT BTN NAME
        print(f'Button "{btnName}" pressed!')

    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////
    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS
    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPosition().toPoint()

        # PRINT MOUSE EVENTS
        if event.buttons() == Qt.LeftButton:
            print("Mouse click: LEFT CLICK")
        if event.buttons() == Qt.RightButton:
            print("Mouse click: RIGHT CLICK")

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
        self.left_row_counter += 1
        self.message_received_count += 1
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
        self.update_receive_send_count()


    @Slot(str)
    def fill_log_window(self, message):
        time_now = datetime.now().strftime("%d/%m/%Y | %H:%M:%S.%f")
        msg = QListWidgetItem(f"{time_now} | {message}")
        if self.log_window.count() >= self.config["other"]["log_window_row_count"]:
            self.log_window.takeItem(0)
        self.log_window.addItem(msg)
        if not self.log_window.hasFocus():
            self.log_window.scrollToBottom()
        self.retranslator.stop()

    def update_receive_send_count(self):
        self.ui.label_receive_send_count.setText(
            f"Receive: {self.message_received_count} / Send: {self.message_sent_count}"
        )

    def start_tcp_client_thread(self):
        # self.signals.data_receive.connect(self.add_row_to_incoming_widget)
        self.signals.data_send.connect(self.add_row_to_outgoing_widget)
        # self.signals.log_data.connect(self.fill_log_window)
        self.tcp_client.connect_to_host("10.32.1.230", 10003)
        # self.ui.pushButton_conn_disconn.setText("Stop server")

    def start_tcp_server_thread(self):
        self.signals.data_receive.connect(self.add_row_to_incoming_widget)
        # self.signals.data_send.connect(self.add_row_to_outgoing_widget)
        self.signals.log_data.connect(self.fill_log_window)
        self.tcp_server.run_server()
        # self.ui.pushButton_conn_disconn.setText("Stop server")

    def start_retranslator_async_thread(self):
        self.signals.data_receive.connect(self.add_row_to_incoming_widget)
        self.signals.data_send.connect(self.add_row_to_outgoing_widget)
        self.signals.log_data.connect(self.fill_log_window)
        self.retranslator.start()
        # self.ui.pushButton_conn_disconn.setText("Stop server")

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
