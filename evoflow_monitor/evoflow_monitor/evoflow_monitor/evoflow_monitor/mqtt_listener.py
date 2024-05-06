import paho.mqtt.client as mqtt
import json
import time
from config import Config
from db.tables_definition.schemas.idec import ReactorState
from evoflow_monitor.tasks import write_to_database


class MqttListener:
    def __init__(self, client_id, broker, port, topic):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()
        self.topic = topic

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        data = json.loads(msg.payload.decode("utf-8"))
        write_to_database(ReactorState, data)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    subscriber = MqttListener(
        client_id="monitor",
        broker="localhost",
        port=1883,
        #broker=Config.MQTT_HOST,
        #port=Config.MQTT_PORT,
        topic="fake_reactor",
    )

    try:
        # Run indefinitely
        while True:
            time.sleep(1)  # Sleep to allow MQTT messages to be processed
    except KeyboardInterrupt:
        # Gracefully stop the subscriber when interrupted
        subscriber.stop()
        print("Subscriber stopped.")
