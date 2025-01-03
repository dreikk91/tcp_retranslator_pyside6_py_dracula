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
            database_engine: str = "sqlite"
            postgres_address: str = "localhost"
            postgres_port: int = 5432
            postgres_database_name: str = "postgres"
            postgres_user: str = "root"
            postgres_password: str = "password"
            sqlite_db_name: str = "base.db"

            # add checks for valid IP addresses and ports
            if not is_valid_ip(clien_host):
                raise ValueError("Invalid client IP address")
            if not is_valid_port(client_port):
                raise ValueError("Invalid client port")
            if server_host and not is_valid_ip(server_host):
                raise ValueError("Invalid server IP address")
            if not is_valid_port(server_port):
                raise ValueError("Invalid server port")
            if not is_valid_db_engine(database_engine):
                raise ValueError("Invalid database engine")

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
                "databases": {
                    "active_engine": database_engine,
                    "postgres": {
                        "postgres_user": postgres_user,
                        "postgres_password": postgres_password,
                        "postgres_address": postgres_address,
                        "postgres_database": postgres_database_name,
                        "postgres_port": postgres_port,
                    },
                    "sqlite": {"sqlite_database_name": sqlite_db_name},
                },
            }
            with open("retranslate.yaml", "w") as f:
                yaml.dump(to_yaml, f, default_flow_style=False)

    def config_open(self) -> Dict[str, Dict[str, Union[str, int]]]:
        try:
            with open("retranslate.yaml") as f:
                yaml_config = yaml.safe_load(f)
        except FileNotFoundError as err:
            logger.exception("Config not found? generating new")
            self.config_init()
            with open("retranslate.yaml") as f:
                yaml_config = yaml.safe_load(f)

        # add checks for valid IP addresses and ports
        if not is_valid_ip(yaml_config["client"]["host"]):
            raise ValueError("Invalid client IP address")
        if not is_valid_port(yaml_config["client"]["port"]):
            raise ValueError("Invalid client port")
        if yaml_config["server"]["host"] and not is_valid_ip(
            yaml_config["server"]["host"]
        ):
            raise ValueError("Invalid server IP address")
        if not is_valid_port(yaml_config["server"]["port"]):
            raise ValueError("Invalid server port")
        if not is_valid_db_engine(yaml_config["databases"]["active_engine"]):
            raise ValueError(
                f'Invalid database engine, must be sqlite or postgres, not {yaml_config["databases"]["active_engine"]}'
            )

        return yaml_config

    def config_save(self, config_data: Dict[str, Dict[str, Union[str, int]]]) -> None:
        with open("retranslate.yaml", "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)


def is_valid_ip(ip: str) -> bool:
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def is_valid_port(port: int) -> bool:
    return 0 <= port <= 65535


def is_valid_db_engine(engine: str) -> bool:
    if engine in ["sqlite", "postgres"]:
        return True
