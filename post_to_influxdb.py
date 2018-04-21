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
import read_ble
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
                    help='Test mode, print messages to stdout instead of sending to Influx')

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
    print("Unable to create database", e)

while True:
    for (mac, ble_payload, rssi) in read_ble.stream_le_advertising_data():
        mac = mac.upper()
        #print(mac, ble_payload, rssi, file=sys.stderr)
        payloads = read_ble.advertising_payloads(ble_payload)
        for type, data in payloads:
            #print(type, data, file=sys.stderr)
            # Manufacturer 0499 in BE == Ruuvitag, Format 3
            if type == 255 and data[0:2] == bytes.fromhex("9904") and data[2] == 3:
                payload = get_decoder(3).decode_data(data.hex())
                if payload is not None:
                    json_body = convert_to_influx(mac, payload)
                    if args.test:
                        print(json_body)
                    else:
                        client.write_points(json_body)
