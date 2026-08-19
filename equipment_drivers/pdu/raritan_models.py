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
    IP_SUFFIX = ""

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
        self.auth = HTTPDigestAuth(self.username, self.password)

        try:
            response = self.session.get(f"{self.base_url}/model/pdu/0", auth=self.auth, timeout=self.timeout)
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


# ==========================================
# Raritan PX2 Series
# ==========================================

class RaritanPx25190RDriver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5190R Switched PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".60"

class RaritanPx25200RDriver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5200R Switched PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".602"

class RaritanPx25440Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5440 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 20
    IP_SUFFIX = ".644"

class RaritanPx25460Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5460 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 30
    IP_SUFFIX = ".61"

class RaritanPx25493Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5493 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".649"

class RaritanPx25524Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5524 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".652"

class RaritanPx25804Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-5804 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 42
    IP_SUFFIX = ".680"

class RaritanPx21493Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX2-1493 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".63"


# ==========================================
# Raritan PX3 Series (Next-Gen Intelligent PDUs)
# ==========================================

class RaritanPx35190RDriver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5190R Switched PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".619"

class RaritanPx35200RDriver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5200R Switched PDU"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".620"

class RaritanPx35440Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5440 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 20
    IP_SUFFIX = ".640"

class RaritanPx35460Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5460 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 30
    IP_SUFFIX = ".61"

class RaritanPx35493Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5493 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".62"

class RaritanPx35524Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5524 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 24
    IP_SUFFIX = ".624"

class RaritanPx35724Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5724 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 36
    IP_SUFFIX = ".672"

class RaritanPx35804Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5804 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 42
    IP_SUFFIX = ".684"

class RaritanPx35904Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan PX3-5904 Switched PDU"
    DEFAULT_CHANNEL_COUNT = 54
    IP_SUFFIX = ".694"


# ==========================================
# Raritan Dominion PX Series
# ==========================================

class RaritanDpxr8a16Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan Dominion PX DPXR8A-16"
    DEFAULT_CHANNEL_COUNT = 8
    IP_SUFFIX = ".64"

class RaritanDpxr12a16Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan Dominion PX DPXR12A-16"
    DEFAULT_CHANNEL_COUNT = 12
    IP_SUFFIX = ".612"

class RaritanDpxr20a16Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan Dominion PX DPXR20A-16"
    DEFAULT_CHANNEL_COUNT = 20
    IP_SUFFIX = ".616"

class RaritanDpxr20a30Driver(BaseRaritanPduDriver):
    MODEL_NAME = "Raritan Dominion PX DPXR20A-30"
    DEFAULT_CHANNEL_COUNT = 20
    IP_SUFFIX = ".630"


# Registry mapping for all 21 Raritan models
RARITAN_MODELS = {
    'raritan_px2_5190r': RaritanPx25190RDriver,
    'raritan_px2_5200r': RaritanPx25200RDriver,
    'raritan_px2_5440': RaritanPx25440Driver,
    'raritan_px2_5460': RaritanPx25460Driver,
    'raritan_px2_5493': RaritanPx25493Driver,
    'raritan_px2_5524': RaritanPx25524Driver,
    'raritan_px2_5804': RaritanPx25804Driver,
    'raritan_px2_1493': RaritanPx21493Driver,
    'raritan_px3_5190r': RaritanPx35190RDriver,
    'raritan_px3_5200r': RaritanPx35200RDriver,
    'raritan_px3_5440': RaritanPx35440Driver,
    'raritan_px3_5460': RaritanPx35460Driver,
    'raritan_px3_5493': RaritanPx35493Driver,
    'raritan_px3_5524': RaritanPx35524Driver,
    'raritan_px3_5724': RaritanPx35724Driver,
    'raritan_px3_5804': RaritanPx35804Driver,
    'raritan_px3_5904': RaritanPx35904Driver,
    'raritan_dpxr8a_16': RaritanDpxr8a16Driver,
    'raritan_dpxr12a_16': RaritanDpxr12a16Driver,
    'raritan_dpxr20a_16': RaritanDpxr20a16Driver,
    'raritan_dpxr20a_30': RaritanDpxr20a30Driver,
}

for sig, driver_cls in RARITAN_MODELS.items():
    registry.register('pdu', sig, driver_cls)
