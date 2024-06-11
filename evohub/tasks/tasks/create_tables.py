from evoflow_db import idec_engine
from evoflow_db.idec import *
from evoflow_db.base import Base
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker


def create_tables():
    with idec_engine().begin() as conn:
        Base.metadata.create_all(conn)


if __name__ == "__main__":
    create_tables()
