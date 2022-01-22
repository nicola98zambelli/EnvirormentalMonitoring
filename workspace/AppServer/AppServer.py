# import
import time
from paho.mqtt.client import Client
import json

# indirizzo IP broker
broker = "172.28.225.99"
port = 1883;

# random client_id
client_id = "mosq-pyAppServer"
username = "chirpstack_as"
password = ""

# topic
device_join_topic = "gateway/1f6aa45e9ed77a78/event/join"
device_up_topic = "gateway/1f6aa45e9ed77a78/event/up"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        print("connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code=", rc)


def on_connect_fail():
    print("connection failed")


def on_disconnect(client, userdata, rc):
    print("client disconnected ok")


def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed to topic ", mid)


def on_message(client, userdata, msg):
    print("Received message: ", msg.payload, " from topic: ", msg.topic)
    print(msg.payload.decode("utf-8"))


def connect_mqtt():
    # Set Connecting Client attributes
    client = Client(client_id=client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_connect_fail = on_connect_fail
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    try:
        print("client connect", client.connect(broker, port, 60))
    except:
        print("ERROR: Could not connect to MQTT.")
    return client


def subscribe(client):
    client.subscribe(device_join_topic)
    client.subscribe(device_up_topic)

def run():
    client = connect_mqtt()
    time.sleep(2)
    try:
        print("in Main Loop")
        subscribe(client)
        client.loop_forever()
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("The 'try except' is finished")


if __name__ == '__main__':
    run()