import pytest
import json
import time
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from evoflow_db.idec import (
    Reactor,
    ExperimentConfig,
    Experiment,
    Base
)

# Under test
from evoflow_listener import mqtt_callbacks 

mock_engine = create_engine('sqlite:///:memory:', echo=False)
Base.metadata.create_all(mock_engine)

@pytest.fixture
def mock_idec_engine(monkeypatch):
    monkeypatch.setattr('evoflow_listener.mqtt_callbacks.db_engine', mock_engine)
   
# Test case for the save_experiment_command_on_db function
def test_save_experiment_command_on_db(mock_idec_engine):
    # Sample test data
    exp_state = {
        "lagoon_temp": 31.36151, 
        "inc_right_temp": 28.57623, 
        "experiment_id": -1, 
        "inc_right_od": -0.187454, 
        "inc_left_dilution": 0, 
        "inc_left_temp": 30.42769, 
        "inc_right_dilution": 0, 
        "inc_left_od": -0.1899156, 
        "timestamp": 1725526793, 
        "lagoon_flow_rate": 0
    }

    # Call the function under test
    mqtt_callbacks.write_experiment_status_to_db(exp_state)

    # no exception means we're fine

