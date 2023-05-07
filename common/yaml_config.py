import logging

import yaml
import pathlib

from common.logger_config import logger


class YamlConfig:
    def __init__(self):
        self.file = pathlib.Path("retranslate.yaml")

    def config_init(self):
        if self.file.exists():
            pass
        else:
            logger.info("Config not exist, generating new")
            clien_host: str = "10.32.1.230"
            client_port: int = 10003
            server_host: str = ""
            server_port: int = 20004
            keepalive: int = 60
            left_window_row_count: int = 1000
            right_window_row_count: int = 1000
            log_window_row_count: int = 1000
            to_yaml: dict = {
                "client": {
                    "host": clien_host,
                    "port": client_port,
                },
                "server": {"host": server_host, "port": server_port},
                "other": {
                    "keepalive": keepalive,
                    "left_window_row_count": left_window_row_count,
                    "right_window_row_count": right_window_row_count,
                    "log_window_row_count": log_window_row_count,
                },
            }
            with open("retranslate.yaml", "w") as f:
                yaml.dump(to_yaml, f, default_flow_style=False)

    def config_open(self):
        with open("retranslate.yaml") as f:
            yaml_config = yaml.safe_load(f)

        return yaml_config
