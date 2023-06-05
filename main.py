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
import asyncio
import logging
import os
import sys
import tracemalloc

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication, QMainWindow

from common.yaml_config import YamlConfig
# from database.sql_part_postgres_async import create_buffer_table_async
# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
from modules.app_settings import Settings
from modules.log_window import LogWindow
from modules.table_widgets import TableManager
from net.retranslator_asyncio.runner import RetranslatorThread
from net.retranslator_asyncio.runner_tcp_client import TCPClientThread
from net.retranslator_asyncio.runner_tcp_server import TCPServerThread
from net.retranslator_asyncio.tcp_client import TCPClient
from net.retranslator_asyncio.tcp_server import ConnectionState, TCPServer

# from net.retranslator_pyside6.runner_pyside6 import TCPClientThread, TCPServerThread
# from net.retranslator_pyside6.tcp_client_pyside6 import TcpClient
# from net.retranslator_pyside6.tcp_server_pyside6 import MyTcpServer

os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    start_signal = Signal()
    done_signal = Signal()
    
    def __init__(self):
        QMainWindow.__init__(self)

        tracemalloc.start()
        

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        self.signals = WorkerSignals()
        # self.signals.start_signal.connect(self.handle_server_status)
        
        self.table_manager = TableManager(widgets)
        self.log_window = LogWindow(widgets)

        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        
        # self.server = TCPServer(self.signals)
        # self.client = TCPClient(
        # self.config["client"]["host"], self.config["client"]["port"], self.signals
        # )
        # self.server_tasks = []
        # self.client_tasks = []
        
        self.server_status = True
        
        self.signals.data_receive.connect(self.table_manager.add_row_to_incoming_widget)
        self.signals.data_send.connect(self.table_manager.add_row_to_outgoing_widget)
        self.signals.log_data.connect(self.log_window.fill_log_window)
        
        # # self.start_tcp_client_thread()
        # self.start_tcp_server_thread()
        self.tcp_server_thread = TCPServerThread(self.signals)
        self.tcp_client_thread = TCPClientThread(self.signals)
        self.start_tcp_server_thread()
        self.start_tcp_client_thread()
        
        # QTimer.singleShot(3, self.start_tcp_client_thread)
        # QTimer.singleShot(3, self.start_tcp_server_thread)

        # QTimer.singleShot(3, self.async_start)

        ConnectionState.is_running.set()


        # Add translations
        widgets.toggleButton.setText(self.tr('Hide'))
        widgets.btn_exit.setText(self.tr('Exit'))
        widgets.btn_home.setText(self.tr('Retranslator'))
        widgets.btn_log.setText(self.tr('log'))

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = False

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = self.tr("TCP Surgurad Retranslator")
        description = self.tr("TCP Surgurad Retranslator APP")
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        widgets.btn_home.clicked.connect(self.buttonClick)
        widgets.btn_log.clicked.connect(self.buttonClick)
        widgets.btn_settings.clicked.connect(self.buttonClick)
        widgets.btn_start_stop.clicked.connect(self.handle_server_status)
        widgets.btn_exit.clicked.connect(self.buttonClick)

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
        themeFile = "themes/py_dracula_light.qss"

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
            
        if btnName == "btn_settings":
            widgets.stackedWidget.setCurrentWidget(widgets.widget_setting)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            
        if btnName == "btn_start_stop":
            self.signals.start_signal.emit()
            

        # # SHOW NEW PAGE
        # if btnName == "btn_new":
        #     widgets.stackedWidget.setCurrentWidget(widgets.new_page) # SET PAGE
        #     UIFunctions.resetStyle(self, btnName) # RESET ANOTHERS BUTTONS SELECTED
        #     btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) # SELECT MENU

        # if btnName == "btn_save":
        #     print("Save BTN clicked!")

        # PRINT BTN NAME
        print(f'Button "{btnName}" pressed!')
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        print("[ Top 10 ]")
        for stat in top_stats[:10]:
            print(stat)
        

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

    # async def setup_server_tasks(self):

    #     self.server_tasks.append(asyncio.create_task(create_buffer_table_async()))
    #     self.server_tasks.append(asyncio.create_task(self.server.run()))
    #     self.server_tasks.append(asyncio.create_task(self.server.write_from_buffer_to_db()))
    #     self.server_tasks.append(asyncio.create_task(self.server.keepalive()))
    #     self.server_tasks.append(asyncio.create_task(self.client.start_tcp_client()))
    #     self.server_tasks.append(asyncio.create_task(self.server.check_connection_state()))
    #     self.group_server = asyncio.create_task(*self.server_tasks, return_exceptions=True)
    #     self.group = asyncio.gather(*self.server_tasks, return_exceptions=True)

    #     try:
    #         await self.group
    #     except asyncio.CancelledError:
    #         print("Tasks cancelled")

    # def stop_server_tasks(self):
    #     while ConnectionState.ready_for_closed:
    #         for task in self.server_tasks:
    #             task.cancel()
    #             print(task)
        
    def handle_server_status(self):
        if self.server_status:
            ConnectionState.server_is_running = False
            self.tcp_server_thread.stop()
            self.tcp_client_thread.stop()
            
            
            widgets.btn_start_stop.setText("Start server")
            widgets.btn_start_stop.setStyleSheet("background-image: url(:/icons/images/icons/cil-media-play.png);")
            self.server_status = False
            
        elif not self.server_status:
            ConnectionState.server_is_running = True
            ConnectionState.ready_for_closed = False
            self.tcp_server_thread.start()
            self.tcp_client_thread.start()
            widgets.btn_start_stop.setText("Stop server")
            widgets.btn_start_stop.setStyleSheet("background-image: url(:/icons/images/icons/cil-media-pause.png);")
            self.server_status = True
            
    # @Slot()
    # def async_start(self):
    #     self.start_signal.emit()
            
    def start_tcp_server_thread(self):
        # tcp_server_thread = TCPServerThread(self.signals)
        self.tcp_server_thread.start()
        
    def start_tcp_client_thread(self):
        # tcp_client_thread = TCPClientThread(self.signals)
        self.tcp_client_thread.start()
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())