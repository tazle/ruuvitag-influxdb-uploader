FROM resin/rpi-raspbian:stretch
RUN apt-get update && apt-get --no-install-recommends -y install python3 python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install setuptools
RUN apt-get install python3-psutil

RUN apt-get install git
CMD python3 post_to_influxdb.py

COPY requirements.txt /
RUN pip3 install -r requirements.txt

COPY read_ble.py post_to_influxdb.py /

