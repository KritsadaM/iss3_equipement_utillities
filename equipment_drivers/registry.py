from typing import Dict, Type, Any, Optional
import logging
from equipment_drivers.interfaces import EquipmentDriver, PDUDriver, TerminalServerDriver, DAQDriver

logger = logging.getLogger(__name__)

class DriverRegistry:
    def __init__(self):
        # Maps equipment type -> signature -> driver class
        # e.g., 'pdu' -> 'apc_dummy_sig' -> DummyPDUDriver
        self._registry: Dict[str, Dict[str, Type[EquipmentDriver]]] = {
            'pdu': {},
            'terminal_server': {},
            'daq': {}
        }

    def register(self, equipment_type: str, signature: str, driver_class: Type[EquipmentDriver]):
        if equipment_type not in self._registry:
            raise ValueError(f"Unknown equipment type: {equipment_type}")
        
        self._registry[equipment_type][signature] = driver_class
        logger.debug(f"Registered driver {driver_class.__name__} for {equipment_type} with signature {signature}")

    def get_driver(self, equipment_type: str, signature: str) -> Optional[Type[EquipmentDriver]]:
        if equipment_type not in self._registry:
            return None
        return self._registry[equipment_type].get(signature)

    def get_all_signatures(self, equipment_type: str) -> list[str]:
        if equipment_type not in self._registry:
            return []
        return list(self._registry[equipment_type].keys())

# Global registry instance
registry = DriverRegistry()
