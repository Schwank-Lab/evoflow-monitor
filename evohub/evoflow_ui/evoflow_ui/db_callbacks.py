import time
import datetime
import json

from evoflow_db import idec_engine
from sqlalchemy import update, select, insert
from sqlalchemy.orm import Session
from evoflow_db.idec import (
    Reactor,
    ExperimentConfig,
    Experiment,
)

db_engine = idec_engine()

def get_reactor_data():
    with Session(db_engine) as session:
        select_stmt = select(Reactor.reactor_id, Reactor.name).order_by(Reactor.name)

        reactor_data = session.execute(select_stmt)
       
    return reactor_data


def pull_reactor_data(reactor_id):
    with Session(db_engine) as session:
        select_stmt = select(Reactor.name, Reactor.network_id).where(
            Reactor.reactor_id == reactor_id
        )
        reactor_data = session.execute(select_stmt).fetchone()

    return reactor_data


def pull_experiment_data(reactor_id):
    with Session(db_engine) as session:
        select_stmt = (
            select(
                Experiment.experiment_id,
                Experiment.name,
                Experiment.inserted_at,
                Experiment.status,
            )
            .where(Experiment.reactor_id == reactor_id)
            .order_by(Experiment.status, Experiment.inserted_at.desc())
        )
        exp_data = session.execute(select_stmt).fetchone()

    return exp_data


def get_reactor_experiment_data(reactor_id):
    reactor_data = pull_reactor_data(reactor_id)
    print(f'db_callbacks#get_reactor_experiment_data reactor_data(reactor_id={reactor_id}): {reactor_data}')
    reactor_data = reactor_data if reactor_data else (None, None)
    
    experiment_data = pull_experiment_data(reactor_id)
    print(f'db_callbacks#get_reactor_experiment_data experiment_data(reactor_id={reactor_id}): {experiment_data}')
    experiment_data = experiment_data if experiment_data else (None, None, None, None)
    
    return reactor_data, experiment_data
    

def update_experiment_state_on_db(reactor_id: int, experiment_id: int, command: str):
    with Session(db_engine) as session:
        update_stmt = (
            update(Experiment)
            .where(Experiment.reactor_id == reactor_id)
            .where(Experiment.experiment_id == experiment_id)
            .values(status=command)
        )
        session.execute(update_stmt)
        session.commit()


def update_experiment_command_on_db(experiment_id: int, experiment_config: json):
    json_string = json.dumps(experiment_config)
    with Session(db_engine) as session:
        update_stmt = (
            update(ExperimentConfig)
            .where(ExperimentConfig.experiment_id == experiment_id)
            .values(exp_config_json=json_string)
        )
        session.execute(update_stmt)
        session.commit()


def save_experiment_command_on_db(reactor_id: int, name: str, experiment_config: json):
    json_string = json.dumps(experiment_config)
    current_timestamp = int(time.time())

    with Session(db_engine) as session:
        stmt = insert(Experiment).values(
            reactor_id=reactor_id,
            name=name,
            timestamp=current_timestamp,
            status="pause",
            inserted_at=datetime.datetime.now()
        )
        result = session.execute(stmt)
        exp_id = result.inserted_primary_key[0]  # Access the newly inserted experiment_id
        print('inserted experiment id', exp_id)
        
        stmt_config = insert(ExperimentConfig).values(
            experiment_id=exp_id,
            exp_config_json=json_string,
            timestamp=current_timestamp,
            inserted_at=datetime.datetime.now(),
        )
        
        # Execute the second insert
        session.execute(stmt_config)
        session.commit()

    return exp_id
