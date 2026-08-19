import logging
from typing import Optional, Tuple
import requests
from requests.auth import HTTPBasicAuth
from equipment_drivers.interfaces import PDUDriver
from equipment_drivers.registry import registry
from equipment_drivers.responses import PDUResponse

logger = logging.getLogger(__name__)


class BaseApcPduDriver(PDUDriver):
    """
    Base driver for APC Switched Rack PDUs (AP79xx / AP89xx series).
    Supports HTTP/REST interaction with APC Network Management Cards.
    """
    MODEL_NAME = "APC Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8
    DEFAULT_PORT = 80

    def __init__(self):
        self.ip = ""
        self.port = self.DEFAULT_PORT
        self.base_url = ""
        self.connected = False
        self.username = "apc"
        self.password = "apc"
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.session = requests.Session()
        self.timeout = 5

    def connect(self, ip: str, port: int, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        self.ip = ip
        self.port = port
        self.base_url = f"http://{self.ip}:{self.port}"
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        self.auth = HTTPBasicAuth(self.username, self.password)

        try:
            response = self.session.get(f"{self.base_url}/rest/v1/device", auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            self.connected = True
            logger.info(f"Connected to {self.get_model()} at {self.ip}:{self.port}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to {self.get_model()} at {self.ip}:{self.port}: {e}")
            raise ConnectionError(f"Connection to APC PDU failed: {e}")

    def disconnect(self) -> bool:
        self.session.close()
        self.connected = False
        logger.info(f"Disconnected from {self.get_model()} at {self.ip}:{self.port}")
        return True

    def get_model(self) -> str:
        return self.MODEL_NAME

    def get_channel_count(self) -> int:
        return self.DEFAULT_CHANNEL_COUNT

    def _control_outlet(self, channel: int, state: str) -> Tuple[bool, str]:
        if not self.connected:
            raise Exception("Not connected to PDU")
        self.validate_channel(channel)

        url = f"{self.base_url}/rest/v1/power/outlets/{channel}"
        payload = {"state": state}
        try:
            response = self.session.put(url, json=payload, auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            return True, response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to control outlet {channel} on {self.get_model()}: {e}")
            raise Exception(f"APC Outlet Control API Error: {e}")

    def turn_on(self, channel: int) -> PDUResponse:
        logger.info(f"Turning ON channel {channel} on {self.get_model()}")
        success, raw = self._control_outlet(channel, "ON")
        return PDUResponse(success=success, action="turn_on", channel=channel, raw=raw)

    def turn_off(self, channel: int) -> PDUResponse:
        logger.info(f"Turning OFF channel {channel} on {self.get_model()}")
        success, raw = self._control_outlet(channel, "OFF")
        return PDUResponse(success=success, action="turn_off", channel=channel, raw=raw)

    def get_status(self, channel: int) -> PDUResponse:
        if not self.connected:
            raise Exception("Not connected to PDU")
        self.validate_channel(channel)

        url = f"{self.base_url}/rest/v1/power/outlets/{channel}"
        try:
            response = self.session.get(url, auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            raw_text = response.text

            state = data.get("state", "").upper()
            status = "ON" if state in ("ON", "1", "TRUE") else ("OFF" if state in ("OFF", "0", "FALSE") else f"UNKNOWN ({state})")
            return PDUResponse(success=True, action="get_status", channel=channel, raw=raw_text, status=status)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get status for outlet {channel} on {self.get_model()}: {e}")
            raise Exception(f"APC Outlet Status API Error: {e}")


# 1. APC AP7900 (1U, 120V 15A, 8 Outlets)
class ApcAp7900Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7900 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.50')


# 2. APC AP7920 (1U, 208/230V 12A, 8 Outlets)
class ApcAp7920Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7920 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.51')


# 3. APC AP7921 (1U, 208/230V 16A, 8 Outlets)
class ApcAp7921Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7921 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.52')


# 4. APC AP8941 (2U 200/208V 30A, 24 Outlets)
class ApcAp8941Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8941 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 24

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.53')


# 5. APC AP8959 (0U 200-240V 24xC13 + 4xC19, 28 Outlets)
class ApcAp8959Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8959 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 28

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.54')


# Register all 5 APC drivers
registry.register('pdu', 'apc_ap7900', ApcAp7900Driver)
registry.register('pdu', 'apc_ap7920', ApcAp7920Driver)
registry.register('pdu', 'apc_ap7921', ApcAp7921Driver)
registry.register('pdu', 'apc_ap8941', ApcAp8941Driver)
registry.register('pdu', 'apc_ap8959', ApcAp8959Driver)
