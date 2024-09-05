from collections import deque
import json
import paho.mqtt.client as mqtt
from evoflow_utils.config import Config
import logging
logging.basicConfig(level=logging.DEBUG)


class MqttCmdCentre:
    def __init__(
        self,
        client_id: str,
        broker: str,
        port: int,
        topics: list[str],
    ):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
            clean_session=False,
            reconnect_on_failure=False,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.enable_logger()
        self.topics = topics
        print(f"MqttCmdCenter#init: Connecting to broker {broker} on port {port}")
        ret_code = self.client.connect(broker, port, 60)
        print(f"MqttCmdCenter#init: Connection result code {str(ret_code)}")
        self.client.loop_start()
        
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("MqttCmdCenter#on_connect: Connected with result code " + str(rc))
        self.client.subscribe([(t, 1) for t in self.topics])

    def on_disconnect(self, client, userdata, rc, *args):
        print(f"Disconnected with result code {rc}", *args)

    def on_message(self, client, userdata, msg):
        print(f"I am the controll centre. This is the topic: {msg.topic}, this is the message {msg}")

    def send_cmds(self, topic, msg):
        print(f"I am the controll centre. This is the topic {topic}, this is the message {msg}")
        self.client.publish(topic, msg)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


class MQTTSubscriber:
    def __init__(self, broker, port, topic):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.message = None
        self.client = mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"MQTTSubscriber#on_connect: Connected with result code {rc}")
        self.client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
        self.message = msg.payload.decode()

    def get_message(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

        while self.message is None:
            pass  # Wait until a message is received

        self.client.loop_stop()
        self.client.disconnect()
        return self.message


def get_mqtt_logs():
    subscriber = MQTTSubscriber(
        broker=str(Config.MQTT_HOST),
        port=int(Config.MQTT_PORT),
        topic="status/experiment",
    )
    return f"{subscriber.get_message()}"


def command_centre():
    cmd_centre = MqttCmdCentre(
        client_id="cmd_centre_local2",
        broker=str(Config.MQTT_HOST),
        port=int(Config.MQTT_PORT),
        topics=["commands"],
    )

    return cmd_centre
