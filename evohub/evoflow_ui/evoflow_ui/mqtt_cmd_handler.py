import paho.mqtt.client as mqtt
from evoflow_utils.config import Config


class MqttCmdCentre:
    def __init__(
        self,
        client_id: str,
        broker: str,
        port: int,
        topics: list[str],
        # topics_handlers: EvohubTopics,
    ):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
        )
        self.client.on_connect = self.on_connect
        self.client.connect(broker, port, 60)
        self.client.loop_start()
        self.topics = topics
        # self.topics_handlers = topics_handlers

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        self.client.subscribe([(t, 1) for t in self.topics])

    def send_cmds(self, topic, msg):
        self.client.publish(topic, msg)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


def command_centre():
    cmd_centre = MqttCmdCentre(
        client_id="cmd_centre",
        broker=str(Config.MQTT_HOST),
        port=int(Config.MQTT_PORT),
        topics=["commands"],
    )

    return cmd_centre
