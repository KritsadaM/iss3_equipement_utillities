from abc import ABC, abstractmethod
from typing import Tuple, Optional
from equipment_drivers.responses import PDUResponse

class EquipmentDriver(ABC):
    @classmethod
    def probe(cls, ip: str, port: int) -> bool:
        """
        Return True if this driver positively identifies the device at ip:port
        as one it can handle. Default is False, so a driver that hasn't
        implemented real detection yet is simply never matched by discovery,
        rather than silently matching everything. Override in concrete
        drivers with real vendor-specific detection.
        """
        return False

    @abstractmethod
    def connect(self, ip: str, port: int, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        username/password are optional overrides for equipment that requires
        auth (e.g. HTTP/SNMP credentials). Drivers with no concept of auth
        (most dummy/simulated drivers) can simply ignore them. Drivers that
        do use credentials should fall back to their own default if these
        are left as None, so existing callers that don't pass them keep working.
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        pass

    @abstractmethod
    def get_model(self) -> str:
        pass

class PDUDriver(EquipmentDriver):
    @abstractmethod
    def turn_on(self, channel: int) -> PDUResponse:
        pass

    @abstractmethod
    def turn_off(self, channel: int) -> PDUResponse:
        pass

    @abstractmethod
    def get_status(self, channel: int) -> PDUResponse:
        pass

class TerminalServerDriver(EquipmentDriver):
    @abstractmethod
    def get_status(self) -> Tuple[str, str]:
        pass

class DAQDriver(EquipmentDriver):
    @abstractmethod
    def start_acquisition(self) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def stop_acquisition(self) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def get_status(self) -> Tuple[str, str]:
        pass
