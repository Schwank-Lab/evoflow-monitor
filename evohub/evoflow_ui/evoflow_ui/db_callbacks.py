import datetime
import json
from evoflow_db import idec_engine
from sqlalchemy import update, select, insert, func
from sqlalchemy.orm import sessionmaker
from evoflow_db.idec import (
    Reactor,
    ExperimentConfig,
    Experiment,
)


def get_reactor_data():
    session_factory = sessionmaker(bind=idec_engine())
    with session_factory() as session:
        select_stmt = select(Reactor.reactor_id, Reactor.name).orderby(Reactor.name)

        reactor_data = session.execute(select_stmt)
        session.commit()
        session.close()

    return reactor_data


def get_reactor_experiment_data(reactor_id):
    session_factory = sessionmaker(bind=idec_engine())
    with session_factory() as session:
        select_stmt = select(Reactor.name, Reactor.network_id).where(
            reactor_id=reactor_id
        )

        reactor_data = session.execute(select_stmt).fetchone()

        select_stmt = (
            select(
                Experiment.experiment_id,
                Experiment.name,
                Experiment.inserted_at,
                Experiment.status,
            )
            .where(status="start")
            .where(reactor_id=reactor_id)
        )

        # Fetch experiment details
        experiment_data = session.execute(select_stmt).fetchone()

        session.commit()
        session.close()

    if reactor_data and experiment_data:
        return reactor_data, experiment_data
    return (None, None), (None, None)


def update_experiment_state_on_db(reactor_id: int, experiment_id: int, command: str):
    session_factory = sessionmaker(bind=idec_engine())
    with session_factory() as session:
        update_stmt = (
            update(Experiment)
            .where(Experiment.reactor_id == reactor_id)
            .where(Experiment.experiment_id == experiment_id)
            .values(status=command)
        )
        session.execute(update_stmt)
        session.commit()
        session.close()


def update_experiment_command_on_db(experiment_id: int, experiment_config: json):
    json_string = json.dumps(experiment_config)
    session_factory = sessionmaker(bind=idec_engine())
    with session_factory() as session:
        update_stmt = (
            update(experiment_config)
            .where(Experiment.experiment_id == experiment_id)
            .values(exp_config_json=json_string)
        )
        session.execute(update_stmt)
        session.commit()
        session.close()


def save_experiment_command_on_db(reactor_id: int, name: str, experiment_config: json):
    session_factory = sessionmaker(bind=idec_engine())
    with session_factory() as session:
        select_stmt = select(func.max(Experiment.experiment_id).label("exp_id")).where(
            Experiment.reactor_id == reactor_id
        )
        experiment_id = session.execute(select_stmt).first()

        insert_stmt = insert(Experiment).values(
            {
                "experiment_id": experiment_id + 1,
                "reactor_id": reactor_id,
                "name": name,
                "timestamp": int(datetime.date.now()),
                "inserted_at": datetime.date.now(),
                "status": "stop",
            }
        )
        session.execute(insert_stmt)
        session.commit()

        json_string = json.dumps(experiment_config)
        select_stmt = select(
            func.max(ExperimentConfig.exp_config_id).label("exp_config_id")
        ).where(Experiment.reactor_id == reactor_id)
        exp_config_id = session.execute(select_stmt).first()

        insert_stmt = insert(ExperimentConfig).values(
            {
                "exp_config_id": exp_config_id + 1,
                "experiment_id": experiment_id,
                "exp_config_json": json_string,
                "timestamp": int(datetime.date.now()),
                "inserted_at": datetime.date.now(),
            }
        )
        session.execute(insert_stmt)
        session.commit()

        session.close()

    return experiment_id
