import unittest
from unittest.mock import patch, MagicMock
import requests
from equipment_drivers.pdu.wti_models import WTI_MODELS, WtiVmrHd4d20Driver


class TestWtiDrivers(unittest.TestCase):
    def setUp(self):
        self.driver_hd20 = WtiVmrHd4d20Driver()
        self.ip = "192.168.1.40"
        self.port = 80

    def test_all_wti_models_registered_and_configured(self):
        self.assertEqual(len(WTI_MODELS), 16)
        for sig, driver_cls in WTI_MODELS.items():
            driver = driver_cls()
            self.assertTrue(driver.get_model().startswith("WTI"))
            self.assertGreater(driver.get_max_channel(), 0)
            self.assertEqual(driver.get_channel_count(), driver.get_max_channel())

    def test_sample_channel_counts(self):
        self.assertEqual(WTI_MODELS['wti_vmr_hd4d20']().get_max_channel(), 20)
        self.assertEqual(WTI_MODELS['wti_vmr_16hd20']().get_max_channel(), 16)
        self.assertEqual(WTI_MODELS['wti_vmr_24hd20']().get_max_channel(), 24)
        self.assertEqual(WTI_MODELS['wti_nps_8hd20']().get_max_channel(), 8)
        self.assertEqual(WTI_MODELS['wti_ips_400']().get_max_channel(), 4)
        self.assertEqual(WTI_MODELS['wti_cpm_1600']().get_max_channel(), 16)

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_connect_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.driver_hd20.connect(self.ip, self.port)
        self.assertTrue(result)
        self.assertTrue(self.driver_hd20.connected)
        mock_get.assert_called_once()

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_connect_with_credential_override(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.driver_hd20.connect(self.ip, self.port, username="custom_user", password="custom_pass")
        self.assertTrue(result)
        self.assertEqual(self.driver_hd20.username, "custom_user")
        self.assertEqual(self.driver_hd20.password, "custom_pass")

    @patch('equipment_drivers.pdu.wti_models.requests.Session.put')
    @patch('equipment_drivers.pdu.wti_models.BaseWtiPduDriver.get_channel_count', return_value=20)
    def test_turn_on(self, mock_count, mock_put):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "OK_RAW"
        mock_put.return_value = mock_response

        response = self.driver_hd20.turn_on(1)
        self.assertTrue(response.success)
        self.assertEqual(response.raw, "OK_RAW")
        self.assertEqual(response.action, "turn_on")
        self.assertEqual(response.channel, 1)

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    @patch('equipment_drivers.pdu.wti_models.BaseWtiPduDriver.get_channel_count', return_value=20)
    def test_get_status_on(self, mock_count, mock_get):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": 1}
        mock_response.text = '{"status": 1}'
        mock_get.return_value = mock_response

        response = self.driver_hd20.get_status(2)
        self.assertEqual(response.status, "ON")
        self.assertEqual(response.raw, '{"status": 1}')
        self.assertTrue(response.success)
        self.assertEqual(response.channel, 2)

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_get_channel_count_from_device(self, mock_get):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": i} for i in range(1, 9)]
        mock_get.return_value = mock_response

        self.assertEqual(self.driver_hd20.get_channel_count(), 8)

    @patch('equipment_drivers.pdu.wti_models.BaseWtiPduDriver.get_channel_count', return_value=20)
    def test_out_of_range_channel_raises_value_error(self, mock_count):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        with self.assertRaises(ValueError):
            self.driver_hd20.turn_on(0)

        with self.assertRaises(ValueError):
            self.driver_hd20.turn_off(21)

        with self.assertRaises(ValueError):
            self.driver_hd20.get_status(-1)


if __name__ == '__main__':
    unittest.main()
