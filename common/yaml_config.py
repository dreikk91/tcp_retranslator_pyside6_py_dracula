import logging
import yaml
import pathlib
import socket
import logging

from typing import Dict, Union

logger = logging.getLogger(__name__)

class YamlConfig:
    def __init__(self) -> None:
        self.file = pathlib.Path("retranslate.yaml")

    def config_init(self) -> None:
        if self.file.exists():
            pass
        else:
            logger.info("Config not exist, generating new")
            clien_host: str = "10.32.1.230"
            client_port: int = 10003
            server_host: str = "0.0.0.0"
            server_port: int = 20005
            keepalive: int = 60
            left_window_row_count: int = 1000
            right_window_row_count: int = 1000
            log_window_row_count: int = 1000

            # add checks for valid IP addresses and ports
            if not is_valid_ip(clien_host):
                raise ValueError("Invalid client IP address")
            if not is_valid_port(client_port):
                raise ValueError("Invalid client port")
            if server_host and not is_valid_ip(server_host):
                raise ValueError("Invalid server IP address")
            if not is_valid_port(server_port):
                raise ValueError("Invalid server port")

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

    def config_open(self) -> Dict[str, Dict[str, Union[str, int]]]:
        with open("retranslate.yaml") as f:
            yaml_config = yaml.safe_load(f)

        # add checks for valid IP addresses and ports
        if not is_valid_ip(yaml_config['client']['host']):
            raise ValueError("Invalid client IP address")
        if not is_valid_port(yaml_config['client']['port']):
            raise ValueError("Invalid client port")
        if yaml_config['server']['host'] and not is_valid_ip(yaml_config['server']['host']):
            raise ValueError("Invalid server IP address")
        if not is_valid_port(yaml_config['server']['port']):
            raise ValueError("Invalid server port")

        return yaml_config


def is_valid_ip(ip: str) -> bool:
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def is_valid_port(port: int) -> bool:
    return 0 <= port <= 65535

# import logging
#
# import yaml
# import pathlib
#
# from common.logger_config import logger
# from typing import Dict, Union
#
#
# class YamlConfig:
#     def __init__(self) -> None:
#         self.file = pathlib.Path("retranslate.yaml")
#
#     def config_init(self) -> None:
#         if self.file.exists():
#             pass
#         else:
#             logger.info("Config not exist, generating new")
#             clien_host: str = "10.32.1.230"
#             client_port: int = 10003
#             server_host: str = ""
#             server_port: int = 20004
#             keepalive: int = 60
#             left_window_row_count: int = 1000
#             right_window_row_count: int = 1000
#             log_window_row_count: int = 1000
#             to_yaml: dict = {
#                 "client": {
#                     "host": clien_host,
#                     "port": client_port,
#                 },
#                 "server": {"host": server_host, "port": server_port},
#                 "other": {
#                     "keepalive": keepalive,
#                     "left_window_row_count": left_window_row_count,
#                     "right_window_row_count": right_window_row_count,
#                     "log_window_row_count": log_window_row_count,
#                 },
#             }
#             with open("retranslate.yaml", "w") as f:
#                 yaml.dump(to_yaml, f, default_flow_style=False)
#
#     def config_open(self) -> Dict[str, Dict[str, Union[str, int]]]:
#         with open("retranslate.yaml") as f:
#             yaml_config = yaml.safe_load(f)
#
#         return yaml_config
