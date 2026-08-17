import logging
from typing import Optional
from equipment_drivers.registry import registry
from equipment_drivers.interfaces import EquipmentDriver

logger = logging.getLogger(__name__)


def discover_and_instantiate(ip: str, port: int, equipment_type: str) -> Optional[EquipmentDriver]:
    """
    Iterates every driver registered for `equipment_type` and asks each one,
    via its probe() classmethod, whether it recognizes the device at ip:port.
    Returns an instance of the first driver that positively identifies itself.

    Drivers registered under the conventional fallback signature
    "dummy_{equipment_type}_sig" are treated as a last-resort match rather
    than being probed -- this preserves the original dev/test behavior where
    an unrecognized device still gets a usable dummy driver instead of
    failing outright. As real probe() detection gets implemented for more
    vendors, this fallback naturally gets used less; it should eventually be
    removed for equipment types where every real driver has proper detection.
    """
    candidates = registry.get_all_drivers(equipment_type)
    if not candidates:
        logger.error(f"No drivers registered for equipment type '{equipment_type}'")
        return None

    logger.info(f"Probing {ip}:{port} against {len(candidates)} registered {equipment_type} driver(s)...")

    fallback_signature = f"dummy_{equipment_type}_sig"
    fallback_class = None

    for signature, driver_class in candidates:
        if signature == fallback_signature:
            # Held back for last -- only used if nothing positively matches.
            fallback_class = driver_class
            continue
        try:
            if driver_class.probe(ip, port):
                logger.info(f"Matched {driver_class.__name__} (signature: {signature}) for {ip}:{port}")
                return driver_class()
        except Exception as e:
            logger.warning(f"probe() raised for {driver_class.__name__} ({signature}): {e}")

    if fallback_class:
        logger.warning(
            f"No driver positively identified {ip}:{port}; falling back to "
            f"{fallback_class.__name__} (signature '{fallback_signature}')."
        )
        return fallback_class()

    logger.error(f"No registered driver could identify device at {ip}:{port}")
    return None
