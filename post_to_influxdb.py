'''
Get data from sensors and write it to InfluxDB

Requires:
    influxdb - pip install influxdb


** Docker InfluxDB & Grafana guide **

Download container
$ docker pull samuelebistoletti/docker-statsd-influxdb-grafana

Create and start new container
$ docker run -d --name docker-statsd-influxdb-grafana -p 3003:3003 -p 3004:8083 -p 8086:8086 -p 22022:22 -p 8125:8125/udp samuelebistoletti/docker-statsd-influxdb-grafana:latest

Or start existing container
$ docker start docker-statsd-influxdb-grafana

InfluxDB: http://localhost:3004/

First create new table: CREATE TABLE tag_data
Query to return all tag data: SELECT * FROM ruuvitag
Remove all data: DROP SERIES FROM ruuvitag

Grafana: http://localhost:3003/ (root/root)

Add datasource (type: InfluxDB url: http://localhost:8086, database: tag_data)
Add new graph to dashboard
'''

import json
from influxdb import InfluxDBClient
from ruuvitag_sensor.ruuvi import RuuviTagSensor

NAMES = json.load(open("mac-mapping.json"))

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
    datas = RuuviTagSensor.get_data_for_sensors()
    json_body = [convert_to_influx(mac, payload) for mac, payload in datas.items()]
    client.write_points(json_body)
