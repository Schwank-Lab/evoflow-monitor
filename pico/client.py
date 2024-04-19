import network
from umqtt.simple import MQTTClient
from time import sleep
import _thread
from math import sin
import uasyncio as asyncio

ssid = "SpaceX"
password = "NelMezzoDelC@mm1n"

STATE_UNKNOWN = 0
STATE_WIFI_NOT_CONNECTED = 1
STATE_WIFI_CONNECTING = 2
STATE_WIFI_CONNECTED = 3

class config:
    mqtt_host = "192.168.10.120"
    mqtt_username = ""  
    mqtt_password = ""  
    mqtt_topic = "io" 
    mqtt_client_id = "pico1"


class Mqtt_Client:
    def __init__(self, wifi_client: Wifi_Client, config):
        self._wifi = wifi_client
        self._config = config
    
    def _set_up_client(self):
        print("Mqtt Client: Setting up client ...")
        self._mqtt_client = MQTTClient(
            client_id=self._config.mqtt_client_id,
            server=self._config.mqtt_host,
            user=self._config.mqtt_username,
            password=self._config.mqtt_password,
        )
        print("Mqtt Client: Setting up client ... Done!")


    def _check_connection(self):
        # check we are online
        self._wifi.check_wifi_connection()
        # check we are connected to mqtt server
        # ...
    
    
    def request_mqtt_connection(self):
#         self._check_connection()
        if self._wifi._state == STATE_WIFI_CONNECTED:
            self._set_up_client()
            print("Mqtt Client: Connecting to broker ...")
            self._mqtt_client.connect()
            print("Mqtt Client: Connecting to broker ... Done")
        else:
            print("Mqtt Client: WiFi not ready ...")

        
    def publish(self, msg):
        if self._wifi._state == STATE_WIFI_CONNECTED:
            self._mqtt_client.publish(self._config.mqtt_topic, msg)
#         elif self._wifi._state == STATE_WIFI_NOT_CONNECTED:
#             self._wifi.cycle()
#             self.publish(msg)


class WiFi_Client:
    def __init__(self):
        self._state = STATE_WIFI_NOT_CONNECTED


    def request_wifi_connection(self):
        print("WiFi Client: Connecting ...")
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        self._wlan.connect(ssid, password)
        while self._wlan.isconnected() == False:
            self._state = STATE_WIFI_CONNECTING
            print("WiFi Client: Waiting for connection")
            sleep(1)
        
        self.check_wifi_connection()
        

    def check_wifi_connection(self):
        if self._wlan.isconnected() == True:
            print("WiFi Client: Connection Established")
            self._gateway_ip = self._wlan.ifconfig()[2]
            print(self._wlan.ifconfig())
            self._state = STATE_WIFI_CONNECTED


def reactor_stuff():
    global counter, m
    while True:
        sine = sin(counter)
        counter += 0.8
        print(str(sine))
        m.publish(str(sine))
        sleep(2)
        
global counter, m
counter = 0
w = WiFi_Client()
m = Mqtt_Client(w, config)

w.request_wifi_connection()
sleep(1)
m.request_mqtt_connection()
sleep(1)
_thread.start_new_thread(reactor_stuff, ())

    

    