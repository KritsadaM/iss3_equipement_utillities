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
    Base driver for APC Switched Rack PDUs (AP79xx / AP89xx / AP86xx series).
    Supports HTTP/REST interaction with APC Network Management Cards.
    """
    MODEL_NAME = "APC Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8
    DEFAULT_PORT = 80
    IP_SUFFIX = ""

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

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        if cls.IP_SUFFIX:
            return ip.endswith(cls.IP_SUFFIX)
        return False

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


# ==========================================
# APC AP79xx Series (1st Gen Switched Rack PDUs)
# ==========================================

class ApcAp7900Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7900 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".50"

class ApcAp7901Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7901 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".501"

class ApcAp7902Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7902 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 16
    IP_SUFFIX = ".502"

class ApcAp7911Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7911 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 16
    IP_SUFFIX = ".511"

class ApcAp7920Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7920 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".51"

class ApcAp7921Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7921 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".52"

class ApcAp7922Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7922 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 16
    IP_SUFFIX = ".522"

class ApcAp7930Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7930 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".530"

class ApcAp7931Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7931 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".531"

class ApcAp7932Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP7932 Switched Rack PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".532"


# ==========================================
# APC AP89xx Series (2nd Gen Switched Rack PDUs)
# ==========================================

class ApcAp8930Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8930 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".590"

class ApcAp8932Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8932 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".592"

class ApcAp8941Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8941 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".53"

class ApcAp8953Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8953 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".553"

class ApcAp8958Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8958 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 20
    IP_SUFFIX = ".558"

class ApcAp8959Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8959 Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 28
    IP_SUFFIX = ".54"

class ApcAp8959Eu3Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8959EU3 3-Phase Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".559"

class ApcAp8965Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8965 3-Phase Switched Rack PDU 2G"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".565"


# ==========================================
# APC AP86xx Series (Metered-by-Outlet with Switching)
# ==========================================

class ApcAp8641Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8641 Switched Rack PDU with Outlet Metering"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".564"

class ApcAp8659Driver(BaseApcPduDriver):
    MODEL_NAME = "APC AP8659 Switched Rack PDU with Outlet Metering"
    DEFAULT_CHANNEL_COUNT = 28
    IP_SUFFIX = ".569"


# Registry mapping for all 20 APC models
APC_MODELS = {
    'apc_ap7900': ApcAp7900Driver,
    'apc_ap7901': ApcAp7901Driver,
    'apc_ap7902': ApcAp7902Driver,
    'apc_ap7911': ApcAp7911Driver,
    'apc_ap7920': ApcAp7920Driver,
    'apc_ap7921': ApcAp7921Driver,
    'apc_ap7922': ApcAp7922Driver,
    'apc_ap7930': ApcAp7930Driver,
    'apc_ap7931': ApcAp7931Driver,
    'apc_ap7932': ApcAp7932Driver,
    'apc_ap8930': ApcAp8930Driver,
    'apc_ap8932': ApcAp8932Driver,
    'apc_ap8941': ApcAp8941Driver,
    'apc_ap8953': ApcAp8953Driver,
    'apc_ap8958': ApcAp8958Driver,
    'apc_ap8959': ApcAp8959Driver,
    'apc_ap8959eu3': ApcAp8959Eu3Driver,
    'apc_ap8965': ApcAp8965Driver,
    'apc_ap8641': ApcAp8641Driver,
    'apc_ap8659': ApcAp8659Driver,
}

for sig, driver_cls in APC_MODELS.items():
    registry.register('pdu', sig, driver_cls)
