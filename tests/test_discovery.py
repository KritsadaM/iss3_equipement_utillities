import unittest
import equipment_drivers
from equipment_drivers.discovery import discover_and_instantiate
from equipment_drivers.pdu.dummy_pdu import DummyPDUDriver
from equipment_drivers.pdu.wti_models import WtiVmrHd4d20Driver

class TestDiscovery(unittest.TestCase):
    def test_discover_dummy_pdu(self):
        driver = discover_and_instantiate("192.168.1.10", 161, "pdu")
        self.assertIsInstance(driver, DummyPDUDriver)

    def test_discover_wti_pdu(self):
        driver = discover_and_instantiate("192.168.1.40", 80, "pdu")
        self.assertIsInstance(driver, WtiVmrHd4d20Driver)

    def test_discover_unknown(self):
        # Should fallback to dummy_pdu_sig in the current implementation
        driver = discover_and_instantiate("192.168.1.99", 161, "pdu")
        self.assertIsInstance(driver, DummyPDUDriver)

if __name__ == '__main__':
    unittest.main()
