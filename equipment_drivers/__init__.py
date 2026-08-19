"""
Importing this package triggers auto-discovery of all driver modules under
pdu/, terminal_server/, and daq/. Each driver module is expected to register
itself against the global registry via the @registry.register(...) decorator
at import time (see registry.py and pdu/wti_models.py for the pattern).

This means adding a new driver is just: drop a new .py file in the right
subfolder with a @registry.register(...)-decorated class. No edits needed
here or in discovery.py.
"""
import pkgutil
import importlib
import os
import logging

logger = logging.getLogger(__name__)

_PACKAGE_DIR = os.path.dirname(__file__)
_DRIVER_SUBPACKAGES = ("pdu", "terminal_server", "daq")

for _subpkg in _DRIVER_SUBPACKAGES:
    _subpkg_path = os.path.join(_PACKAGE_DIR, _subpkg)
    if not os.path.isdir(_subpkg_path):
        continue
    for _finder, _module_name, _is_pkg in pkgutil.iter_modules([_subpkg_path]):
        _full_name = f"{__name__}.{_subpkg}.{_module_name}"
        try:
            importlib.import_module(_full_name)
        except Exception as e:
            logger.error(f"Failed to import driver module {_full_name}: {e}")
