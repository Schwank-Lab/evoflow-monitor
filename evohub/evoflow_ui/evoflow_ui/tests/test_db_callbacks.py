import pytest
import json
import time
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from evoflow_ui import db_callbacks
from evoflow_db.idec import (
    Reactor,
    ExperimentConfig,
    Experiment,
    Base
)
mock_engine = create_engine('sqlite:///:memory:', echo=False)
Base.metadata.create_all(mock_engine)

@pytest.fixture
def mock_idec_engine(monkeypatch):
    monkeypatch.setattr('evoflow_ui.db_callbacks.db_engine', mock_engine)
   
# Test case for the save_experiment_command_on_db function
def test_save_experiment_command_on_db(mock_idec_engine):
    # Sample test data
    reactor_id = 1
    name = "Test Experiment"
    experiment_config = {"param1": "value1", "param2": 10}
    
    # Call the function under test
    experiment_id = db_callbacks.save_experiment_command_on_db(reactor_id, name, experiment_config)
    
    with Session(mock_engine) as session:
        # Query the database to verify the Experiment was inserted
        exp = session.query(Experiment).filter_by(experiment_id=experiment_id).one_or_none()
        assert exp is not None, "Experiment was not added to the database"
        assert exp.reactor_id == reactor_id
        assert exp.name == name
        assert exp.status == "pause"
        
        # Query the database to verify the ExperimentConfig was inserted
        exp_conf = session.query(ExperimentConfig).filter_by(experiment_id=experiment_id).one_or_none()
        assert exp_conf is not None, "ExperimentConfig was not added to the database"
        assert exp_conf.exp_config_json == json.dumps(experiment_config)


# Test case for the update_experiment_command_on_db function
def test_update_experiment_command_on_db(mock_idec_engine):
    # Set up initial experiment and experiment config
    initial_config = {"param1": "initial_value", "param2": 5}
    updated_config = {"param1": "updated_value", "param2": 10}

    # First, insert an experiment and experiment config into the database
    reactor_id = 1
    name = "Test Experiment"
    
    # Save the experiment and configuration
    experiment_id = db_callbacks.save_experiment_command_on_db(reactor_id, name, initial_config)
    
    # Now, update the experiment configuration using the function being tested
    db_callbacks.update_experiment_command_on_db(experiment_id, updated_config)
    
    # Query the database to verify the ExperimentConfig was updated
    with Session(mock_engine) as session:
        exp_conf = session.query(ExperimentConfig).filter_by(experiment_id=experiment_id).one_or_none()
        assert exp_conf is not None, "ExperimentConfig was not found in the database"
        assert exp_conf.exp_config_json == json.dumps(updated_config), "ExperimentConfig was not updated correctly"


# Test case for the update_experiment_state_on_db function
def test_update_experiment_state_on_db(mock_idec_engine):
    # Initial data setup
    initial_config = {"param1": "initial_value", "param2": 5}
    initial_status = "paused"
    updated_status = "running"
    
    # Insert an experiment into the database
    reactor_id = 1
    name = "Test Experiment"
    
    # Save the experiment
    experiment_id = db_callbacks.save_experiment_command_on_db(reactor_id, name, initial_config)
    
    # Verify the initial status of the experiment
    with Session(mock_engine) as session:
        exp = session.query(Experiment).filter_by(experiment_id=experiment_id).one_or_none()
        assert exp is not None, "Experiment was not added to the database"
        assert exp.status == "pause", "Initial experiment status is incorrect"
    
    # Now, update the experiment state using the function being tested
    db_callbacks.update_experiment_state_on_db(reactor_id, experiment_id, updated_status)
    
    # Verify that the status was updated in the database
    with Session(mock_engine) as session:
        exp = session.query(Experiment).filter_by(experiment_id=experiment_id).one_or_none()
        assert exp is not None, "Experiment was not found in the database"
        assert exp.status == updated_status, "Experiment status was not updated correctly"