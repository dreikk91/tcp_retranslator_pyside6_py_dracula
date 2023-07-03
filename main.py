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
import logging
import os
import sys
import tracemalloc

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from common.yaml_config import YamlConfig
# from database.sql_part_postgres_async import create_buffer_table_async
# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from modules import *
from modules.app_settings import Settings
from modules.config_page import ConfigPage
from modules.log_window import LogWindow
from modules.table_widgets import TableManager
from net.retranslator_asyncio.runner_tcp_client import EventForwarderThread
from net.retranslator_asyncio.runner_tcp_server import TCPServerThread
from net.retranslator_asyncio.tcp_server import ConnectionState


os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        tracemalloc.start()

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.widgets = self.ui

        self.signals = WorkerSignals()
        # self.signals.start_signal.connect(self.handle_server_status)
        
        self.table_manager = TableManager(self.widgets)
        self.log_window = LogWindow(self.widgets)
        self.config_page = ConfigPage(self.widgets)

        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        
        self.server_status = True
        
        self.signals.data_receive.connect(self.table_manager.add_row_to_incoming_widget)
        self.signals.data_send.connect(self.table_manager.add_row_to_outgoing_widget)
        self.signals.log_data.connect(self.log_window.fill_log_window)
        self.signals.objects_activity.connect(self.table_manager.add_row_to_objects_table)
        
        self.tcp_server_thread = TCPServerThread(self.signals)
        self.tcp_client_thread = EventForwarderThread(self.signals)
        self.start_tcp_server_thread()
        self.start_tcp_client_thread()
        

        ConnectionState.is_running.set()


        # Add translations
        self.widgets.toggleButton.setText(self.tr('Hide'))
        self.widgets.btn_exit.setText(self.tr('Exit'))
        self.widgets.btn_home.setText(self.tr('Terminal'))
        self.widgets.btn_log.setText(self.tr('log'))

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = False

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = self.tr("TCP Surgurad Retranslator")
        description = self.tr("TCP Surgurad Retranslator APP")
        # APPLY TEXTS
        self.setWindowTitle(title)
        self.widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        self.widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.ui_definitions(self)

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        self.widgets.btn_home.clicked.connect(self.button_click)
        self.widgets.btn_log.clicked.connect(self.button_click)
        self.widgets.btn_settings.clicked.connect(self.button_click)
        self.widgets.btn_start_stop.clicked.connect(self.handle_server_status)
        self.widgets.btn_exit.clicked.connect(self.button_click)
        self.widgets.btn_objects.clicked.connect(self.button_click)
    

        # widgets.btn_new.clicked.connect(self.buttonClick)
        # widgets.btn_save.clicked.connect(self.buttonClick)

        # EXTRA LEFT BOX
        def open_close_left_box():
            UIFunctions.toggle_left_box(self, True)

        self.widgets.toggleLeftBox.clicked.connect(open_close_left_box)
        self.widgets.extraCloseColumnBtn.clicked.connect(open_close_left_box)

        # EXTRA RIGHT BOX
        def open_close_right_box():
            UIFunctions.toggle_right_box(self, True)

        self.widgets.settingsTopBtn.clicked.connect(open_close_right_box)

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        use_custom_theme = True
        theme_file = "themes/py_dracula_light.qss"

        # SET THEME AND HACKS
        if use_custom_theme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, theme_file, True)

            # SET HACKS
            AppFunctions.set_theme_hack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        self.widgets.stackedWidget.setCurrentWidget(self.widgets.widget_retranslator)
        self.widgets.btn_home.setStyleSheet(
            UIFunctions.selectMenu(self.widgets.btn_home.styleSheet())
        )

    # BUTTONS CLICK
    # Post here your functions for clicked buttons
    # ///////////////////////////////////////////////////////////////
    def button_click(self):      
        # GET BUTTON CLICKED
        btn = self.sender()
        btn_name = btn.objectName()

        # SHOW HOME PAGE
        if btn_name == "btn_home":
            self.widgets.stackedWidget.setCurrentWidget(self.widgets.widget_retranslator)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            
        if btn_name == "btn_objects":
            self.widgets.stackedWidget.setCurrentWidget(self.widgets.widget_objects)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            

        # SHOW WIDGETS PAGE
        if btn_name == "btn_log":
            self.widgets.stackedWidget.setCurrentWidget(self.widgets.widget_log)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            
        if btn_name == "btn_settings":
            self.widgets.stackedWidget.setCurrentWidget(self.widgets.widget_setting)
            UIFunctions.resetStyle(self, btn_name)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            
        if btn_name == "btn_start_stop":
            self.signals.start_signal.emit()
            

        # # SHOW NEW PAGE
        # if btnName == "btn_new":
        #     widgets.stackedWidget.setCurrentWidget(widgets.new_page) # SET PAGE
        #     UIFunctions.resetStyle(self, btnName) # RESET ANOTHERS BUTTONS SELECTED
        #     btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) # SELECT MENU

        # if btnName == "btn_save":
        #     print("Save BTN clicked!")

        # PRINT BTN NAME
        print(f'Button "{btn_name}" pressed!')
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

        
    def handle_server_status(self):
        if self.server_status:
            ConnectionState.server_is_running = False
            self.tcp_server_thread.stop()
            self.tcp_client_thread.stop()
            
            
            self.widgets.btn_start_stop.setText("Start server")
            self.widgets.btn_start_stop.setStyleSheet("background-image: url(:/icons/images/icons/cil-media-play.png);")
            self.server_status = False
            
        elif not self.server_status:
            ConnectionState.server_is_running = True
            ConnectionState.ready_for_closed = False
            self.tcp_server_thread.start()
            self.tcp_client_thread.start()
            self.widgets.btn_start_stop.setText("Stop server")
            self.widgets.btn_start_stop.setStyleSheet("background-image: url(:/icons/images/icons/cil-media-pause.png);")
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