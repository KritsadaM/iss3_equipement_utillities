from abc import ABC, abstractmethod
from typing import Tuple

class EquipmentDriver(ABC):
    @abstractmethod
    def connect(self, ip: str, port: int) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        pass

    @abstractmethod
    def get_model(self) -> str:
        pass

class PDUDriver(EquipmentDriver):
    @abstractmethod
    def turn_on(self, channel: int) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def turn_off(self, channel: int) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def get_status(self, channel: int) -> Tuple[str, str]:
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
