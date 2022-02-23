from datetime import datetime
import time
import json
import base64
from paho.mqtt.client import Client

from enums.bcolors import BColors
from utils.api_utils import enqueue_device_downlink
from utils.app_server_utils import getWatchdogAppServer, getWatchdogConfiguration


class AppServer:
    # Topics
    # Subscribe topics
    up_topic = "application/%s/device/%s/event/up"
    status_topic = "application/%s/device/%s/event/status"
    join_topic = "application/%s/device/%s/event/join"

    def __init__(self, broker="", port=None, id_application="", application_name="", ip="localhost",
                 network_server_id=None):
        self.broker = broker
        self.port = port
        self.ip = ip
        self.client = None
        self.client_id = "loraappserver" + str(id_application)
        self.username = "chirpstack_as"
        self.password = ""
        self.id_application = id_application
        self.application_name = application_name
        self.can_sand_data = False
        self.watchdogs = dict()

    def start_connection(self):
        try:
            # Set Connecting Client ID
            self.client = Client(client_id=self.client_id)
            self.client.username_pw_set(self.username, self.password)

            # call back functions
            self.client.on_connect = self.on_connect
            self.client.on_connect_fail = self.on_connect_fail
            self.client.on_disconnect = self.on_disconnect
            self.client.on_subscribe = self.on_subscribe
            self.client.on_message = self.on_message

            print(f"{BColors.OKGREEN.value}AppServer "
                  f"connect: {self.client.connect(self.broker, self.port, 60)} {BColors.ENDC.value}")
            time.sleep(1)
            self.client.loop_start()

            while not self.client.is_connected():
                print(f"{BColors.OKGREEN.value}Wait for connection{BColors.ENDC.value}")
                time.sleep(1)

            print("Client connected!")
        except BaseException as err:
            print(f"{BColors.WARNING.value}ERROR: AppServer Could not connect to MQTT.{BColors.ENDC.value}")
            print(f"{BColors.FAIL.value}Unexpected {err=}, {type(err)=}{BColors.ENDC.value}")
            self.close_connection()

    def subscribe(self, devEUI):
        join_topic_to_sub = AppServer.join_topic % (self.id_application, devEUI)
        up_topic_to_sub = AppServer.up_topic % (self.id_application, devEUI)
        status_topic_to_sub = AppServer.status_topic % (self.id_application, devEUI)

        self.client.subscribe(join_topic_to_sub)
        self.client.subscribe(up_topic_to_sub)
        self.client.subscribe(status_topic_to_sub)

    def close_connection(self):
        self.client.loop_stop()
        self.client.disconnect()

    # call back functions
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.client.connected_flag = True
            print(f"{BColors.OKGREEN.value}Connected OK Returned code={rc}{BColors.ENDC.value}")
        else:
            print(f"{BColors.FAIL.value}Bad connection Returned code={rc}{BColors.ENDC.value}")

    def on_connect_fail(self):
        print(f"{BColors.FAIL.value}AppServer connection failed{BColors.ENDC.value}")

    def on_disconnect(self, client, userdata, rc):
        print(f"{BColors.OKGREEN.value}AppServer disconnected with code={rc}{BColors.ENDC.value}")

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print(f"{BColors.OKGREEN.value}AppServer subscribed to topic {mid}{BColors.ENDC.value}")

    def on_message(self, client, userdata, msg):
        print(f"{BColors.OKGREEN.value}AppServer received message from topic: {msg.topic}{BColors.ENDC.value}")
        topic_splitted = msg.topic.split("/")
        topic_type = topic_splitted[-2] + topic_splitted[-1]
        payload_decoded = json.loads(msg.payload.decode())
        if topic_type == "eventjoin":
            devEUI_decoded = base64.b64decode(payload_decoded['devEUI'].encode()).hex()
            self.watchdogs[devEUI_decoded] = getWatchdogAppServer(payload_decoded)
        elif topic_type == "eventup":
            devEUI_decoded = base64.b64decode(payload_decoded['devEUI'].encode()).hex()
            self.watchdogs[devEUI_decoded].last_seen = round(datetime.now().timestamp())

        elif topic_type == "eventstatus":
            devEUI_decoded = base64.b64decode(payload_decoded['devEUI'].encode()).hex()
            self.watchdogs[devEUI_decoded].watchdog.batteryLevel = payload_decoded['batteryLevel']
            self.watchdogs[devEUI_decoded].watchdog.batteryLevelUnavailable = payload_decoded['batteryLevelUnavailable']
            self.watchdogs[devEUI_decoded].watchdog.margin = payload_decoded['margin']
            self.watchdogs[devEUI_decoded].last_seen = round(datetime.now().timestamp())
            watchdog_configuration = getWatchdogConfiguration()
            string_to_send = json.dumps(watchdog_configuration.toJson())
            string_to_send_encoded = base64.b64encode(string_to_send.encode()).decode()
            enqueue_device_downlink(devEUI_decoded, 1, False, string_to_send_encoded)
            

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)