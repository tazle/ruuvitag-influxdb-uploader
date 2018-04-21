'''
Get data from sensors and write it to InfluxDB

Requires:
    influxdb - pip install influxdb

Does not run LE scanning, that must be done externally.
'''

import json
import sys
from influxdb import InfluxDBClient
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.decoder import get_decoder
from ruuvitag_sensor.ble_communication import BleCommunicationBleson
import argparse

mappings = sys.stdin.read()
try:
    NAMES = json.loads(mappings)
except Exception as e:
    print(mappings)
    NAMES = {}

parser = argparse.ArgumentParser(description='Send RuuviTag observations to InfluxDB.')
parser.add_argument('--test', dest='test', action='store_const',
                    const=True, default=False,
                    help="Test mode, don't send to Influx")
parser.add_argument('--quiet', dest='quiet', action='store_const',
                    const=True, default=False,
                    help="Quiet mode, don't print messages to stdout")

args = parser.parse_args()


def convert_to_influx(mac, payload):
    return {
        "measurement": "ruuvitag",
        "tags": {
            "mac": mac,
            "name": NAMES.get(mac, "Unknown")
        },
        "fields": {
            "temperature": payload["temperature"],
            "humidity": payload["humidity"],
            "pressure": payload["pressure"],
            "battery": payload["battery"],
            "acceleration": payload["acceleration"],
            "acceleration_x": payload["acceleration_x"],
            "acceleration_y": payload["acceleration_y"],
            "acceleration_z": payload["acceleration_z"]
        }
    }


client = InfluxDBClient(host="localhost", port=8086, database="tag_data")

try:
    client.create_database('tag_data')
except Exception as e:
    print("Unable to create database", e, file=sys.stderr)

while True:
    for mac, data in BleCommunicationBleson.get_datas():
        #print(mac, data)
        if data[0:2] == bytes.fromhex("9904") and data[2] == 3:
            payload = get_decoder(3).decode_data(data[2:])
            if payload is not None:
                json_body = convert_to_influx(mac, payload)
                if not args.quiet:
                    print(json_body)
                if not args.test:
                    client.write_points([json_body])
                    
