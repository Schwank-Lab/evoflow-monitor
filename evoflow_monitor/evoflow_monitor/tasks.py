from prefect import task
from db.tables_definition.base import Base
from db.utilities import idec_engine
from db.tables_definition.schemas.idec import Reactor
from sqlalchemy import insert


@task
def create_tables():
    with idec_engine().begin() as conn:
        Base.metadata.create_all(conn)


@task
def write_to_database(table: Base, data: dict):
    with idec_engine().connect() as conn:
        insert_stmt = insert(table).values(**data)
        conn.execute(insert_stmt)
        conn.commit()


@task
def decode_mqqt_message():
    pass


@task
def publish_mqtt_message():
    pass


# task
def subscribe_mqtt_message():
    pass
