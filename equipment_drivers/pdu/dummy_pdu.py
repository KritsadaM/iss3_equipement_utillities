import logging
from typing import Tuple
from equipment_drivers.interfaces import PDUDriver
from equipment_drivers.registry import registry

logger = logging.getLogger(__name__)

class DummyPDUDriver(PDUDriver):
    def __init__(self):
        self.ip = ""
        self.port = 0
        self.connected = False

    def connect(self, ip: str, port: int) -> bool:
        self.ip = ip
        self.port = port
        self.connected = True
        logger.info(f"Connected to Dummy PDU at {ip}:{port}")
        return True

    def disconnect(self) -> bool:
        self.connected = False
        logger.info(f"Disconnected from Dummy PDU at {self.ip}:{self.port}")
        return True

    def get_model(self) -> str:
        return "Dummy PDU Model X"

    def turn_on(self, channel: int) -> Tuple[bool, str]:
        if not self.connected:
            raise Exception("Not connected to PDU")
        logger.info(f"Turning ON channel {channel} on Dummy PDU")
        raw_output = f"DUMMY_RAW: Channel {channel} set to 1"
        return True, raw_output

    def turn_off(self, channel: int) -> Tuple[bool, str]:
        if not self.connected:
            raise Exception("Not connected to PDU")
        logger.info(f"Turning OFF channel {channel} on Dummy PDU")
        raw_output = f"DUMMY_RAW: Channel {channel} set to 0"
        return True, raw_output

    def get_status(self, channel: int) -> Tuple[str, str]:
        if not self.connected:
            raise Exception("Not connected to PDU")
        logger.info(f"Checking status for channel {channel} on Dummy PDU")
        raw_output = f"DUMMY_RAW: Channel {channel} is 1"
        return "ON", raw_output

# Register the driver
registry.register('pdu', 'dummy_pdu_sig', DummyPDUDriver)
