from prefect import task
from db.tables_definition.schemas.idec import *
from db import idec_engine
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker


# @task
def create_tables():
    with idec_engine().begin() as conn:
        Base.metadata.create_all(conn)


# @task
def write_to_database(table: Base, data: dict):
    session_factory = sessionmaker(bind=idec_engine())
    with session_factory() as session:
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


if __name__ == "__main__":
    create_tables()
