import logging
import requests
from requests.auth import HTTPBasicAuth
from equipment_drivers.interfaces import PDUDriver
from equipment_drivers.registry import registry
from equipment_drivers.responses import PDUResponse

logger = logging.getLogger(__name__)

from typing import Tuple


class WtiVmrHd4d20Driver(PDUDriver):
    """
    Driver for the WTI VMR-HD4D20 C19 Power Distribution Unit.
    Communicates via the WTI REST API.
    """

    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        """
        Identifies a WTI VMR-HD4D20 at ip:port. This is currently the same
        IP-suffix simulation used elsewhere in the project (no real hardware
        to probe yet) -- once real units are reachable, replace this with an
        actual check, e.g. a GET to /api/v2/status with a short timeout and
        checking the response for a WTI-identifying field, wrapped so any
        connection error just returns False rather than raising.
        """
        return ip.endswith('.40')

    def __init__(self):
        self.ip = ""
        self.port = 80
        self.base_url = ""
        self.connected = False

        # Default credentials; in a real app, these should be passed via config
        self.username = "admin"
        self.password = "admin"
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.session = requests.Session()

        # Timeout for API requests (seconds)
        self.timeout = 5

    def connect(self, ip: str, port: int, username: str = None, password: str = None) -> bool:
        self.ip = ip
        self.port = port
        self.base_url = f"http://{self.ip}:{self.port}/api/v2"

        # Override credentials if the caller provided them; otherwise keep
        # the defaults set in __init__.
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        self.auth = HTTPBasicAuth(self.username, self.password)

        # Test connection by fetching the device info
        try:
            response = self.session.get(f"{self.base_url}/status", auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            self.connected = True
            logger.info(f"Connected to WTI VMR-HD4D20 at {self.ip}:{self.port}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to WTI PDU at {self.ip}:{self.port}: {e}")
            raise ConnectionError(f"Connection to WTI PDU failed: {e}")

    def disconnect(self) -> bool:
        self.session.close()
        self.connected = False
        logger.info(f"Disconnected from WTI PDU at {self.ip}:{self.port}")
        return True

    def get_model(self) -> str:
        return "WTI VMR-HD4D20 C19"

    def _control_plug(self, channel: int, action: int) -> Tuple[bool, str]:
        """
        Internal method to control a plug.
        action: 1 for ON, 0 for OFF
        """
        if not self.connected:
            raise Exception("Not connected to PDU")

        url = f"{self.base_url}/plugs/{channel}"
        payload = {"action": action}

        try:
            response = self.session.put(url, json=payload, auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            return True, response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to control plug {channel} on WTI PDU: {e}")
            raise Exception(f"WTI Plug Control API Error: {e}")

    def turn_on(self, channel: int) -> PDUResponse:
        logger.info(f"Turning ON channel {channel} on WTI PDU")
        success, raw = self._control_plug(channel, 1)
        return PDUResponse(success=success, action="turn_on", channel=channel, raw=raw)

    def turn_off(self, channel: int) -> PDUResponse:
        logger.info(f"Turning OFF channel {channel} on WTI PDU")
        success, raw = self._control_plug(channel, 0)
        return PDUResponse(success=success, action="turn_off", channel=channel, raw=raw)

    def get_status(self, channel: int) -> PDUResponse:
        if not self.connected:
            raise Exception("Not connected to PDU")

        url = f"{self.base_url}/plugs/{channel}"

        try:
            response = self.session.get(url, auth=self.auth, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            raw_text = response.text

            # Assuming the API returns something like {"status": 1}
            status_code = data.get("status")
            if status_code == 1:
                status = "ON"
            elif status_code == 0:
                status = "OFF"
            else:
                status = f"UNKNOWN ({status_code})"
            return PDUResponse(success=True, action="get_status", channel=channel, raw=raw_text, status=status)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get status for plug {channel} on WTI PDU: {e}")
            raise Exception(f"WTI Plug Status API Error: {e}")


# Register the driver
registry.register('pdu', 'wti_vmr_hd4d20', WtiVmrHd4d20Driver)
