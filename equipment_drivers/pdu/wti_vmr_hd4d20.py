import logging
import requests
from requests.auth import HTTPBasicAuth
from equipment_drivers.interfaces import PDUDriver
from equipment_drivers.registry import registry

logger = logging.getLogger(__name__)

from typing import Tuple

class WtiVmrHd4d20Driver(PDUDriver):
    """
    Driver for the WTI VMR-HD4D20 C19 Power Distribution Unit.
    Communicates via the WTI REST API.
    """
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

    def connect(self, ip: str, port: int) -> bool:
        self.ip = ip
        self.port = port
        self.base_url = f"http://{self.ip}:{self.port}/api/v2"
        
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

    def turn_on(self, channel: int) -> Tuple[bool, str]:
        logger.info(f"Turning ON channel {channel} on WTI PDU")
        return self._control_plug(channel, 1)

    def turn_off(self, channel: int) -> Tuple[bool, str]:
        logger.info(f"Turning OFF channel {channel} on WTI PDU")
        return self._control_plug(channel, 0)

    def get_status(self, channel: int) -> Tuple[str, str]:
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
                return "ON", raw_text
            elif status_code == 0:
                return "OFF", raw_text
            else:
                return f"UNKNOWN ({status_code})", raw_text
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get status for plug {channel} on WTI PDU: {e}")
            raise Exception(f"WTI Plug Status API Error: {e}")

# Register the driver
registry.register('pdu', 'wti_vmr_hd4d20', WtiVmrHd4d20Driver)
