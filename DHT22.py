#!/usr/bin/env python3

import json
import re
import time
import sys
from paho.mqtt import client as mqtt_client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

import board
import adafruit_dht

# ==== CONFIGURATION ==== #

# MQTT settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "Temp_and_Humidity"
MQTT_CLIENT_ID = "mqtt2influx_bridge"

# DHT sensor settings
DHT_PIN = board.D4  # adjust if your data pin is a different GPIO

# Regex to parse payload “Temp: 24.0 °C, Hum: 44.4 %”
payload_re = re.compile(r"Temp:\s*([0-9]+\.[0-9]+)\s*°C,\s*Hum:\s*([0-9]+\.[0-9]+)\s*%")

# ==== FUNCTIONS ==== #

def load_influx_config(json_path):
    """Load INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET from JSON file."""
    try:
        with open(json_path, "r") as f:
            j = json.load(f)
        url = j.get("INFLUX_URL")
        token = j.get("INFLUX_TOKEN")
        org = j.get("INFLUX_ORG")
        bucket = j.get("INFLUX_BUCKET")
        if not (url and token and org and bucket):
            raise ValueError("One or more InfluxDB config values missing in JSON")
        return url, token, org, bucket
    except Exception as e:
        print("Failed to load Influx config from JSON:", e)
        sys.exit(1)

def connect_mqtt():
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, MQTT_CLIENT_ID)
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            client.subscribe(MQTT_TOPIC)
        else:
            print("Failed to connect to MQTT Broker, return code:", rc)
            sys.exit(1)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT)
    return client

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip()
    print(f"Received {topic} : {payload}")

    m = payload_re.match(payload)
    if not m:
        print("Payload did not match expected format, skipping.")
        return

    temp = float(m.group(1))
    hum = float(m.group(2))

    p = (
        Point("temperature_humidity")
        .field("temperature", temp)
        .field("humidity", hum)
    )

    try:
        write_api = userdata["write_api"]
        write_api.write(bucket=userdata["bucket"], org=userdata["org"], record=p)
        print("Wrote point to InfluxDB:", p.to_line_protocol())
    except Exception as e:
        print("Error writing to InfluxDB:", e)

def read_dht():
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        print(f"DEBUG: DHT read temp={temperature}, hum={humidity}")
        if temperature is None or humidity is None:
            raise RuntimeError("DHT returned None")
        return temperature, humidity
    except Exception as e:
        print("Error reading DHT:", e)
        return None, None

def main():
    global sensor

    # Load Influx config
    json_path = "/home/......../APIInfluxDB.json"   #Update your path here
    INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET = load_influx_config(json_path)

    # Initialize the DHT sensor
    sensor = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)

    print("Connecting to InfluxDB at", INFLUX_URL)
    influx_client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    # Setup MQTT client
    mqtt = connect_mqtt()
    # Pass write_api + config into userdata
    mqtt.user_data_set({
        "write_api": write_api,
        "org": INFLUX_ORG,
        "bucket": INFLUX_BUCKET
    })
    mqtt.on_message = on_message

    print("Starting loop to read sensor, publish to MQTT, and write to InfluxDB...")
    mqtt.loop_start()

    try:
        while True:
            temp, hum = read_dht()
            if temp is not None and hum is not None:
                payload = f"Temp: {temp:.1f} °C, Hum: {hum:.1f} %"
                print("Publishing MQTT:", payload)
                mqtt.publish(MQTT_TOPIC, payload)
            else:
                print("Skipping publishing due to read failure")

            time.sleep(30)
    except KeyboardInterrupt:
        print("Interrupted by user, exiting.")
    finally:
        try:
            sensor.exit()
        except Exception:
            pass
        mqtt.loop_stop()
        mqtt.disconnect()

if __name__ == "__main__":
    main()
