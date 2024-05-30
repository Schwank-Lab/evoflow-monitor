from evoflow_db import idec_engine
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker
from evoflow_db.idec import (
    Reactor,
    ReactorConfig,
    ExperimentState,
    ExpConfig,
    Experiment,
)


def write_to_database(
    table: Reactor | ReactorConfig | ExperimentState | ExpConfig | Experiment,
    data: dict,
):
    session_factory = sessionmaker(bind=idec_engine())
    with session_factory() as session:
        insert_stmt = insert(table).values(**data)
        session.execute(insert_stmt)
        session.commit()
        session.close()


def write_experiment_status_to_db(data: dict):
    print("Write experiment data to db")
    del data["reactor_id"]
    print(data)
    write_to_database(ExperimentState, data)


def write_reactor_status_to_db(data: dict):
    print("Write reactor status to db")


def parse_logs_experiment(data: dict):
    print("Parsing logs")


def parse_logs_reactor(data: dict):
    print("Parsing reactor logs")


def parse_experiment_commands(data: dict):
    print("Parse experiment commands")


def parse_reactor_commands(data: dict):
    print("Parse reactor commands")
