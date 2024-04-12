import paho.mqtt.client as mqtt
import time
import json


class MqttClient:
    def __init__(self, client_id, broker, port, topic):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.topic = topic

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe("fake_reactor")

    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        data = json.loads(msg.payload)
        print(data)

    def publish(self, data):
        self.client.publish("fake_reactor", json.dumps(data))

    def loop(self):
        self.client.loop_start()
        while True:
            time.sleep(1)
            self.publish({"temperature": 25, "humidity": 50})


if __name__ == "__main__":
    client = MqttClient("fake_reactor", "192.168.10.111", 1883, "fake_reactor")
    client.loop()
