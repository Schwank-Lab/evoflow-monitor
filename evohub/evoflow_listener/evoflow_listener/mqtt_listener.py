import sys
import time
import logging
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker

from evoflow_utils.mqtt_client import MqttClient
from evoflow_utils.config import Config
from evoflow_db.idec import ExperimentState
from evoflow_db import idec_engine

db_engine = idec_engine()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)


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


def create_experiment_status_listener():
    return MqttClient(
        client_id="monitor",
        broker=str(Config.MQTT_HOST),
        port=int(Config.MQTT_PORT),
        topics_handlers={
            "status/experiment": write_experiment_status_to_db
        },
    )


def main():
    subscriber = create_experiment_status_listener()
    try:
        logger.info("Subscriber Started.")
        # Run indefinitely
        while True:
            time.sleep(1)  # Sleep to allow MQTT messages to be processed
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    except KeyboardInterrupt:
        # Gracefully stop the subscriber when interrupted
        subscriber.stop()
        logger.info("Subscriber stopped.")
