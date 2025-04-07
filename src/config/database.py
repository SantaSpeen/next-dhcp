from dataclasses import dataclass

from core import InvalidDatabaseConfiguration

@dataclass
class DataBaseConfiguration:
    """Class for storing the configuration of the database"""
    driver: str = "sqlite"
    database: str = "nextdhcp.db"
    host: str = None
    port: int = None
    user: str = None
    password: str = None

    def __post_init__(self):
        self.check()
        if self.driver == "sqlite":
            from piccolo.engine.sqlite import SQLiteEngine
            self._engine = SQLiteEngine(self.database)
        elif self.driver == "psql":
            from piccolo.engine.postgres import PostgresEngine
            self._engine = PostgresEngine(config={
                "database": self.database,
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.password,
            })
        elif self.driver == "cockdb":
            from piccolo.engine.cockroach import CockroachEngine
            self._engine = CockroachEngine(config={
                "database": self.database,
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "password": self.password,
            })

    def check(self):
        if self.driver not in ("sqlite", "psql", "cockdb"):
            raise InvalidDatabaseConfiguration("Invalid database driver. Supported: sqlite, psql, cockdb")

    @property
    def engine(self):
        """Get the database engine"""
        return self._engine
