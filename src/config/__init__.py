import os
from pathlib import Path

from .database import DataBaseConfiguration
from .dhcp import DHCPServerConfiguration


class Config:
    path = Path("config.json")

    def __init__(self):
        self._database = DataBaseConfiguration()
        self._dhcp = DHCPServerConfiguration()

    def _read_environment(self):
        # Database configuration
        db_driver = os.environ.get("DB_DRIVER")
        if db_driver not in ("sqlite", "psql", "cockdb"):
            raise ValueError("Invalid database driver. Supported: sqlite, psql, cockdb")
        db_database = os.environ.get("DB_DATABASE")
        db_host = os.environ.get("DB_HOST")
        db_port = os.environ.get("DB_PORT")
        db_username = os.environ.get("DB_USERNAME")
        db_password = os.environ.get("DB_PASSWORD")

