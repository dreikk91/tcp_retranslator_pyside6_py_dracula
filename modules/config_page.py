import yaml
from common.yaml_config import YamlConfig

class ConfigPage:
    def __init__(self, widgets):
        self.yc = YamlConfig()
        self.yc.config_init()
        self.config = self.yc.config_open()
        self.ui = widgets
        
        self.client_host:str = ''
        self.client_port: int = 0
        
        self.server_address: str = ''
        self.server_port: int = 0
        self.server_keepalive: int = 60
        
        self.database_engine_active: str = ''
        
        self.postgres_address: str = ''
        self.postgres_port: int = 0
        self.postgres_username:str = ''
        self.postgres_password: str = ''
        self.postgres_database: str = ''
        
        self.sqlite_database_name:str = ''
        
        self.left_table_row_count: int = 0
        self.right_table_row_count: int = 0
        self.log_list_row_count: int = 0
        self.init_config()
        self.ui.pushButton_settings_save.clicked.connect(self.save_config)
        
            
    def init_config(self):
        self.server_address = str(self.config['server']['host'])
        self.server_port = str(self.config['server']['port'])
        self.server_keepalive = str(self.config['other']['keepalive'])

        self.client_host = str(self.config['client']['host'])
        self.client_port = str(self.config['client']['port'])

        self.postgres_address = str(self.config['databases']['postgres']['postgres_address'])
        self.postgres_password = str(self.config['databases']['postgres']['postgres_password'])
        self.postgres_username = str(self.config['databases']['postgres']['postgres_user'])
        self.postgres_database = str(self.config['databases']['postgres']['postgres_database'])
        
        self.sqlite_database_name = str(self.config['databases']['sqlite']['sqlite_database_name'])
        self.database_engine_active = str(self.config['databases']['active_engine'])
        
        self.left_table_row_count = str(self.config['other']['left_window_row_count'])
        self.right_table_row_count = str(self.config['other']['right_window_row_count'])
        self.log_list_row_count = str(self.config['other']['log_window_row_count'])
        
        self.ui.comboBox_database_engine.addItems(['postgres', 'sqlite'])
        
        self.ui.lineEdit_server_address.setText(self.server_address)
        self.ui.lineEdit_server_port.setText(self.server_port)
        self.ui.lineEdit_keepalive_timeout.setText(self.server_keepalive)
        
        self.ui.lineEdit_client_address.setText(self.client_host)
        self.ui.lineEdit_client_port.setText(self.client_port)
        
        self.ui.lineEdit_settings_postgres_address.setText(self.postgres_address)
        self.ui.lineEdit_settings_postgres_password.setText(self.postgres_password)
        self.ui.lineEdit_settings_postgres_username.setText(self.postgres_username)
        self.ui.lineEdit_postgres_database_name.setText(self.postgres_database)
        
        self.ui.lineEdit_settings_sqlite_path.setText(self.sqlite_database_name)
        
        
        self.ui.lineEdit_log_list_row_count.setText(self.log_list_row_count)
        self.ui.lineEdit_incoming_table_row_count.setText(self.left_table_row_count)
        self.ui.lineEdit_outgoing_table_row_count.setText(self.right_table_row_count)
        
        self.ui.comboBox_database_engine.addItems(['postgres', 'sqlite'])
    
    def retrieve_data(self):
        self.server_address = self.ui.lineEdit_server_address.text()
        self.server_port = int(self.ui.lineEdit_server_port.text())
        self.server_keepalive = int(self.ui.lineEdit_keepalive_timeout.text())

        self.client_host = self.ui.lineEdit_client_address.text()
        self.client_port = int(self.ui.lineEdit_client_port.text())

        self.postgres_address = self.ui.lineEdit_settings_postgres_address.text()
        self.postgres_password = self.ui.lineEdit_settings_postgres_password.text()
        self.postgres_username = self.ui.lineEdit_settings_postgres_username.text()
        self.postgres_database = self.ui.lineEdit_postgres_database_name.text()

        self.sqlite_database_name = self.ui.lineEdit_settings_sqlite_path.text()

        self.left_table_row_count = int(self.ui.lineEdit_incoming_table_row_count.text())
        self.right_table_row_count = int(self.ui.lineEdit_outgoing_table_row_count.text())
        self.log_list_row_count = int(self.ui.lineEdit_log_list_row_count.text())

        self.database_engine_active = self.ui.comboBox_database_engine.currentText()

    def save_config(self):
        self.retrieve_data()
        self.config['server']['host'] = self.server_address
        self.config['server']['port'] = self.server_port
        self.config['other']['keepalive'] = self.server_keepalive

        self.config['client']['host'] = self.client_host
        self.config['client']['port'] = self.client_port

        self.config['databases']['postgres']['postgres_address'] = self.postgres_address
        self.config['databases']['postgres']['postgres_password'] = self.postgres_password
        self.config['databases']['postgres']['postgres_user'] = self.postgres_username
        self.config['databases']['postgres']['postgres_database'] = self.postgres_database

        self.config['databases']['sqlite']['sqlite_database_name'] = self.sqlite_database_name

        self.config['other']['left_window_row_count'] = self.left_table_row_count
        self.config['other']['right_window_row_count'] = self.right_table_row_count
        self.config['other']['log_window_row_count'] = self.log_list_row_count
        self.config['databases']['active_engine'] = self.database_engine_active

        self.yc.config_save(self.config)