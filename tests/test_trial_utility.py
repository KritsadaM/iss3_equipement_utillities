import unittest
from equipment_drivers.simulator import MockPduServer, run_pdu_blackbox_trial
from equipment_drivers.pdu.apc_models import ApcAp7900Driver
from equipment_drivers.pdu.wti_models import WtiVmrHd4d20Driver
from equipment_drivers.pdu.raritan_models import RaritanPx35460Driver


class TestSimulatorAndTrialUtility(unittest.TestCase):
    def test_mock_apc_server(self):
        with MockPduServer(vendor="apc", channel_count=8) as server:
            driver = ApcAp7900Driver()
            self.assertTrue(driver.connect(server.host, server.port))
            self.assertEqual(driver.get_max_channel(), 8)

            resp_on = driver.turn_on(1)
            self.assertTrue(resp_on.success)
            self.assertIn("success", resp_on.raw)

            resp_status = driver.get_status(1)
            self.assertEqual(resp_status.status, "ON")

            resp_off = driver.turn_off(1)
            self.assertTrue(resp_off.success)

            driver.disconnect()

    def test_mock_wti_server(self):
        with MockPduServer(vendor="wti", channel_count=20) as server:
            driver = WtiVmrHd4d20Driver()
            self.assertTrue(driver.connect(server.host, server.port))
            self.assertEqual(driver.get_max_channel(), 20)

            resp_on = driver.turn_on(5)
            self.assertTrue(resp_on.success)

            resp_off = driver.turn_off(5)
            self.assertTrue(resp_off.success)

            driver.disconnect()

    def test_mock_raritan_server(self):
        with MockPduServer(vendor="raritan", channel_count=30) as server:
            driver = RaritanPx35460Driver()
            self.assertTrue(driver.connect(server.host, server.port))
            self.assertEqual(driver.get_max_channel(), 30)

            resp_on = driver.turn_on(10)
            self.assertTrue(resp_on.success)

            resp_off = driver.turn_off(10)
            self.assertTrue(resp_off.success)

            driver.disconnect()

    def test_run_pdu_blackbox_trial(self):
        self.assertTrue(run_pdu_blackbox_trial("apc_ap7900", ApcAp7900Driver))
        self.assertTrue(run_pdu_blackbox_trial("wti_vmr_hd4d20", WtiVmrHd4d20Driver))
        self.assertTrue(run_pdu_blackbox_trial("raritan_px3_5460", RaritanPx35460Driver))


if __name__ == '__main__':
    unittest.main()
