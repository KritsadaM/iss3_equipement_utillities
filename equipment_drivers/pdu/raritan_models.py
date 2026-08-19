import logging
from typing import Optional, Tuple
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from equipment_drivers.interfaces import PDUDriver
from equipment_drivers.registry import registry
from equipment_drivers.responses import PDUResponse

logger = logging.getLogger(__name__)


class BaseRaritanPduDriver(PDUDriver):
    """
    Base driver for Raritan Intelligent Rack PDUs (PX2, PX3, Dominion PX series).
    Communicates via Raritan JSON-RPC / REST API (Xerus OS).
    """
    MODEL_NAME = "Raritan Intelligent Rack PDU"
    DEFAULT_CHANNEL_COUNT = 8
    DEFAULT_PORT = 80

    def __init__(self):
        self.ip = ""
        self.port = self.DEFAULT_PORT
        self.base_url = ""
        self.connected = False
        self.username = "admin"
        self.password = "raritan"
        self.auth = HTTPDigestAuth(self.username, self.password)
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
        self.auth = HTTPDigestAuth(self.username, self.password)

        try:
            response = self.session.get(f"{self.base_url}/model/pdu/0", auth=self.auth, timeout=self.timeout)
            # Try basic auth if digest auth fails (some firmware versions support basic auth)
            if response.status_code == 401:
                self.auth = HTTPBasicAuth(self.username, self.password)
                response = self.session.get(f"{self.base_url}/model/pdu/0", auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            self.connected = True
            logger.info(f"Connected to {self.get_model()} at {self.ip}:{self.port}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to {self.get_model()} at {self.ip}:{self.port}: {e}")
            raise ConnectionError(f"Connection to Raritan PDU failed: {e}")

    def disconnect(self) -> bool:
        self.session.close()
        self.connected = False
        logger.info(f"Disconnected from {self.get_model()} at {self.ip}:{self.port}")
        return True

    def get_model(self) -> str:
        return self.MODEL_NAME

    def get_channel_count(self) -> int:
        return self.DEFAULT_CHANNEL_COUNT

    def _control_outlet(self, channel: int, power_state: int) -> Tuple[bool, str]:
        """
        power_state: 1 for ON (close), 0 for OFF (open)
        Raritan uses 0-indexed outlet internal mapping (channel 1 -> outlet 0).
        """
        if not self.connected:
            raise Exception("Not connected to PDU")
        self.validate_channel(channel)

        outlet_idx = channel - 1
        url = f"{self.base_url}/model/outlet/{outlet_idx}"
        payload = {"powerState": power_state}
        try:
            response = self.session.put(url, json=payload, auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            return True, response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to control outlet {channel} on {self.get_model()}: {e}")
            raise Exception(f"Raritan Outlet Control API Error: {e}")

    def turn_on(self, channel: int) -> PDUResponse:
        logger.info(f"Turning ON channel {channel} on {self.get_model()}")
        success, raw = self._control_outlet(channel, 1)
        return PDUResponse(success=success, action="turn_on", channel=channel, raw=raw)

    def turn_off(self, channel: int) -> PDUResponse:
        logger.info(f"Turning OFF channel {channel} on {self.get_model()}")
        success, raw = self._control_outlet(channel, 0)
        return PDUResponse(success=success, action="turn_off", channel=channel, raw=raw)

    def get_status(self, channel: int) -> PDUResponse:
        if not self.connected:
            raise Exception("Not connected to PDU")
        self.validate_channel(channel)

        outlet_idx = channel - 1
        url = f"{self.base_url}/model/outlet/{outlet_idx}"
        try:
            response = self.session.get(url, auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            raw_text = response.text

            power_state = data.get("powerState", 0)
            status = "ON" if power_state in (1, "1", "on", "ON", "closed") else "OFF"
            return PDUResponse(success=True, action="get_status", channel=channel, raw=raw_text, status=status)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get status for outlet {channel} on {self.get_model()}: {e}")
            raise Exception(f"Raritan Outlet Status API Error: {e}")


# 1. Raritan PX2-5190R (1U/2U Switched, 8 Outlets)
class RaritanPx25190RDriver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5190R Switched PDU"
    DEFAULT_CHANNEL_COUNT = 8

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.60')


# 2. Raritan PX3-5460 (0U Switched & Metered, 30 Outlets)
class RaritanPx35460Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5460 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 30

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.61')


# 3. Raritan PX3-5493 (0U Switched, 24 Outlets)
class RaritanPx35493Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5493 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 24

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.62')


# 4. Raritan PX2-1493 (0U Switched, 24 Outlets)
class RaritanPx21493Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-1493 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 24

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.63')


# 5. Raritan DPXR8A-16 (Dominion PX 8-Port Switched, 8 Outlets)
class RaritanDpxr8a16Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan Dominion PX DPXR8A-16"
    DEFAULT_CHANNEL_COUNT = 8

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        return ip.endswith('.64')


# Register all 5 Raritan drivers
registry.register('pdu', 'raritan_px2_5190r', RaritanPx25190RDriver)
registry.register('pdu', 'raritan_px3_5460', RaritanPx35460Driver)
registry.register('pdu', 'raritan_px3_5493', RaritanPx35493Driver)
registry.register('pdu', 'raritan_px2_1493', RaritanPx21493Driver)
registry.register('pdu', 'raritan_dpxr8a_16', RaritanDpxr8a16Driver)
