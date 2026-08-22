import unittest
from unittest.mock import patch, MagicMock
import threading
import time

import equipment_drivers  # noqa: trigger driver registration
from equipment_drivers.simulator import MockPduServer, run_pdu_blackbox_trial, run_pdu_mock_action, determine_vendor
from equipment_drivers.pdu.apc_models import ApcAp7900Driver
from equipment_drivers.pdu.wti_models import WtiVmrHd4d20Driver
from equipment_drivers.pdu.raritan_models import RaritanPx35460Driver


class TestMockPduServer(unittest.TestCase):

    def test_apc_mock_server_starts_and_stops(self):
        server = MockPduServer(vendor="apc", channel_count=8)
        server.start()
        self.assertIsNotNone(server.server)
        self.assertGreater(server.port, 0)
        server.stop()
        self.assertIsNone(server.server)

    def test_wti_mock_server_starts_and_stops(self):
        with MockPduServer(vendor="wti", channel_count=20) as server:
            self.assertGreater(server.port, 0)

    def test_raritan_mock_server_starts_and_stops(self):
        with MockPduServer(vendor="raritan", channel_count=30) as server:
            self.assertGreater(server.port, 0)

    def test_ephemeral_port_allocation(self):
        with MockPduServer(vendor="apc", port=0) as s1:
            with MockPduServer(vendor="apc", port=0) as s2:
                self.assertNotEqual(s1.port, s2.port)


class TestDetermineVendor(unittest.TestCase):

    def test_apc_from_signature(self):
        self.assertEqual(determine_vendor("apc_ap7900", ApcAp7900Driver), "apc")

    def test_wti_from_signature(self):
        self.assertEqual(determine_vendor("wti_vmr_hd4d20", WtiVmrHd4d20Driver), "wti")

    def test_raritan_from_signature(self):
        self.assertEqual(determine_vendor("raritan_px3_5460", RaritanPx35460Driver), "raritan")

    def test_unknown_defaults_apc(self):
        self.assertEqual(determine_vendor("unknown_x999", ApcAp7900Driver), "apc")


class TestRunPduBlackboxTrial(unittest.TestCase):

    def test_apc_full_trial_passes(self):
        result = run_pdu_blackbox_trial("apc_ap7900", ApcAp7900Driver, verbose=True)
        self.assertTrue(result)

    def test_wti_full_trial_passes(self):
        result = run_pdu_blackbox_trial("wti_vmr_hd4d20", WtiVmrHd4d20Driver, verbose=True)
        self.assertTrue(result)

    def test_raritan_full_trial_passes(self):
        result = run_pdu_blackbox_trial("raritan_px3_5460", RaritanPx35460Driver, verbose=True)
        self.assertTrue(result)


class TestRunPduMockAction(unittest.TestCase):

    def test_apc_mock_on(self):
        result = run_pdu_mock_action("apc_ap7900", ApcAp7900Driver, "on", "1", verbose=True)
        self.assertTrue(result)

    def test_apc_mock_off(self):
        result = run_pdu_mock_action("apc_ap7900", ApcAp7900Driver, "off", "1", verbose=True)
        self.assertTrue(result)

    def test_apc_mock_status(self):
        result = run_pdu_mock_action("apc_ap7900", ApcAp7900Driver, "status", "1", verbose=True)
        self.assertTrue(result)

    def test_wti_mock_status_multi_channel(self):
        result = run_pdu_mock_action("wti_vmr_hd4d20", WtiVmrHd4d20Driver, "status", "1-3", verbose=True)
        self.assertTrue(result)

    def test_raritan_mock_action_all(self):
        result = run_pdu_mock_action("raritan_px3_5460", RaritanPx35460Driver, "status", "all", verbose=True)
        self.assertTrue(result)

    def test_invalid_channel_returns_false(self):
        result = run_pdu_mock_action("apc_ap7900", ApcAp7900Driver, "on", "999", verbose=False)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
