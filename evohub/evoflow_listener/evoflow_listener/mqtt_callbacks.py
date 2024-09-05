from evoflow_db import idec_engine
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker
from evoflow_db.idec import (
    Reactor,
    ReactorConfig,
    ExperimentState,
    ExperimentConfig,
    Experiment,
)

db_engine = idec_engine()

def write_to_database(
    table: Reactor | ReactorConfig | ExperimentState | ExperimentConfig | Experiment,
    data: dict,
):
    session_factory = sessionmaker(bind=db_engine)
    with session_factory() as session:
        insert_stmt = insert(table).values(**data)
        session.execute(insert_stmt)
        session.commit()


def write_experiment_status_to_db(data: dict):
    print("Write experiment data to db")
    session_factory = sessionmaker(bind=db_engine)
    with session_factory() as session:
        insert_stmt = insert(ExperimentState).values(
            lagoon_temp=data["lagoon_temp"],
            inc_right_temp=data["inc_right_temp"],
            experiment_id=data["experiment_id"],
            inc_right_od=data["inc_right_od"],
            inc_left_dilution=data["inc_left_dilution"],
            inc_left_temp=data["inc_left_temp"],
            inc_right_dilution=data["inc_right_dilution"],
            inc_left_od=data["inc_left_od"],
            timestamp=data["timestamp"],
            lagoon_flow_rate=data["lagoon_flow_rate"],
        )
        session.execute(insert_stmt)
        session.commit()



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
