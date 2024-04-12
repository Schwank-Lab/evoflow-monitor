import paho.mqtt.client as mqtt
import json
import time


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
        data = json.loads(msg.payload)
        print(data)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    subscriber = MqttListener(
        client_id="monitor",
        broker="192.168.10.111",
        port=1883,
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

    # try:
    #     client = mqtt.Client(
    #         mqtt.CallbackAPIVersion.VERSION2,
    #         "ciccio",
    #     )
    #     client.on_connect = on_connect
    #     client.on_message = on_message
    #     client.connect("192.168.10.111", 1883, 60)
    #     client.loop_start()
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     client.loop_stop()
    #     client.disconnect()
    #     print("Subscriber stopped.")
