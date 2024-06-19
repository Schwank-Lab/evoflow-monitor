import time
import datetime
import json

from evoflow_db import idec_engine
from sqlalchemy import update, select, func
from sqlalchemy.orm import Session
from evoflow_db.idec import (
    Reactor,
    ExperimentConfig,
    Experiment,
)


def get_reactor_data():
    with Session(idec_engine()) as session:
        select_stmt = select(Reactor.reactor_id, Reactor.name).order_by(Reactor.name)

        reactor_data = session.execute(select_stmt)
        session.commit()
        session.close()

    return reactor_data


def pull_reactor_data(reactor_id):
    with Session(idec_engine()) as session:
        select_stmt = select(Reactor.name, Reactor.network_id).where(
            Reactor.reactor_id == reactor_id
        )
        reactor_data = session.execute(select_stmt).fetchone()
        session.close()

    return reactor_data


def pull_experiment_data(reactor_id):
    with Session(idec_engine()) as session:
        select_stmt = (
            select(
                Experiment.experiment_id,
                Experiment.name,
                Experiment.inserted_at,
                Experiment.status,
            )
            .where(Experiment.status == "start")
            .where(Experiment.reactor_id == reactor_id)
        )
        exp_data = session.execute(select_stmt).fetchone()
        session.close()

    return exp_data


def get_reactor_experiment_data(reactor_id):
    reactor_data = pull_reactor_data(reactor_id)
    experiment_data = pull_experiment_data(reactor_id)

    if reactor_data and experiment_data:
        return reactor_data, experiment_data
    return (None, None), (None, None, None, None)


def update_experiment_state_on_db(reactor_id: int, experiment_id: int, command: str):
    with Session(idec_engine()) as session:
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
    with Session(idec_engine()) as session:
        update_stmt = (
            update(ExperimentConfig)
            .where(ExperimentConfig.experiment_id == experiment_id)
            .values(exp_config_json=json_string)
        )
        session.execute(update_stmt)
        session.commit()
        session.close()


def save_experiment_command_on_db(reactor_id: int, name: str, experiment_config: json):
    json_string = json.dumps(experiment_config)
    exp = Experiment(
        reactor_id=reactor_id,
        name=name,
        timestamp=int(time.time()),
        status="pause",
    )
    with Session(idec_engine()) as session:
        session.add(exp)
        exp_id = session.execute(
            select(func.max(Experiment.experiment_id)).where(
                Reactor.reactor_id == reactor_id
            )
        ).fetchone()[0]
        print(exp_id)
        exp_conf = ExperimentConfig(
            experiment_id=exp_id,
            exp_config_json=json_string,
            timestamp=int(time.time()),
            inserted_at=datetime.datetime.now(),
        )

        session.add(exp_conf)
        session.commit()
        session.close()

    return exp_id
