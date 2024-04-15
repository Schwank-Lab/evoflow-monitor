from pathlib import Path
import paho.mqtt.client as mqtt
import json
import time
from csv_reader import CSVReader


class MqttClient:
    def __init__(self, client_id, broker, port, topic):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
        )
        self.client.on_connect = self.on_connect
        self.client.connect(broker, port, 60)
        self.topic = topic

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        client.subscribe(self.topic)

    def publish(self, data):
        self.client.publish(self.topic, data)


if __name__ == "__main__":
    file = (
        Path(__file__).parent.parent.parent
        / "evoflow_monitor"
        / "data"
        / "20240305_pace_state.csv"
    )

    client = MqttClient(
        client_id="fake_reactor",
        broker="192.168.10.111",
        port=1883,
        topic="fake_reactor",
    )
    reader = CSVReader(file)
    for l in reader.to_json():
        time.sleep(1)
        client.publish(l)
