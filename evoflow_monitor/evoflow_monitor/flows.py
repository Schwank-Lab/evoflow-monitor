from prefect import flow
from db.tables_definition.schemas.idec import Reactor
from tasks import create_tables, write_to_database


@flow
def table_creation():
    create_tables()


@flow
def add_reactor_to_fleet():
    write_to_database(
        Reactor, {"reactor_id": 1, "name": "Test Reactor", "network_id": "192.168.1.2"}
    )


@flow
def add_experiment():
    pass


if __name__ == "__main__":
    insert_reactor_data()
