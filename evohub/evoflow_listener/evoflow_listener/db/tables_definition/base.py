from sqlalchemy.orm import MappedAsDataclass
from sqlalchemy.orm import DeclarativeBase


class Base(MappedAsDataclass, DeclarativeBase):
    __abstract__ = True

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __str__(self):
        return str(self.__dict__)


# Path: evoflow_monitor/db/tables_definition/monitor.py
