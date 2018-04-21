import socket
import struct
import select
import sys
from construct import RawCopy
from hci_protocol.hci_protocol import HciPacket, HciPacketType, HciEventType, LeMetaEventSubtype

class HciSniffer(object):
    def __init__(self, hci_device_number=0):
        print("Binding socket", file=sys.stderr)
        self._hci_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
        self._hci_socket.setsockopt(socket.SOL_HCI, socket.HCI_DATA_DIR, 1)
        self._hci_socket.setsockopt(socket.SOL_HCI, socket.HCI_TIME_STAMP, 1)
        self._hci_socket.setsockopt(
            socket.SOL_HCI, socket.HCI_FILTER, struct.pack("IIIH2x", 0xffffffff, 0xffffffff, 0xffffffff, 0)
        )
        self._hci_socket.bind((hci_device_number,))
        self._hci_device_number = hci_device_number
        print("Socket created and bound", file=sys.stderr)

    def stream(self):
        while True:
            readable, _, _ = select.select([self._hci_socket], [], [])
            if readable is not None:
                packet = self._hci_socket.recv(4096)
                yield RawCopy(HciPacket).parse(packet)

def stream_le_advertising_data(macs=[]):
    hci_sniffer = HciSniffer()
    for packet_and_data in hci_sniffer.stream():
        packet = packet_and_data.value
        if packet.type == HciPacketType.EVENT_PACKET:
            if packet.payload.event == HciEventType.LE_META_EVENT:
                meta_event = packet.payload.payload
                if meta_event.subevent == LeMetaEventSubtype.LE_ADVERTISING_REPORT:
                    report = meta_event.payload
                    for i in range(report.num_reports):
                        addr = report.addresses[i]
                        rssi = report.rssis[i]
                        if not macs or addr in macs:
                            data = "".join("%02x" % d for d in report.datas[i])
                            yield (addr, data, rssi)

def advertising_payloads(advertising_frame):
    b = bytes.fromhex(advertising_frame)
    parts = []
    while b:
        if b[0] == 0:
            # Section lenth cannot be 0, 0 means we have encountered garbage, let's no try to parse further
            raise ValueError("Invalid advertising frame " + advertising_frame)
        section = b[:b[0]+1]
        b = b[b[0]+1:]
        sec_type = section[1]
        sec_data = section[2:]
        parts.append((sec_type, sec_data))
    return parts
