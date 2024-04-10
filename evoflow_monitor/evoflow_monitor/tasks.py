from prefect import task
from db.tables_definition.base import Base
from db import idec_engine, session
from sqlalchemy import insert


@task
def create_tables():
    with idec_engine().begin() as conn:
        Base.metadata.create_all(conn)


@task
def write_to_database(table: Base, data: dict):
    with session() as session:
        insert_stmt = insert(table).values(**data)
        session.execute(insert_stmt)
        session.commit()
        session.close()


@task
def decode_mqqt_message():
    pass


@task
def publish_mqtt_message():
    pass


# task
def subscribe_mqtt_message():
    pass
