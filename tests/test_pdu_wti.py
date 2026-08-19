import unittest
from unittest.mock import patch, MagicMock
import requests
from equipment_drivers.pdu.wti_vmr_hd4d20 import WtiVmrHd4d20Driver

class TestWtiVmrHd4d20Driver(unittest.TestCase):
    def setUp(self):
        self.driver = WtiVmrHd4d20Driver()
        self.ip = "192.168.1.40"
        self.port = 80

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.get')
    def test_connect_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.driver.connect(self.ip, self.port)
        self.assertTrue(result)
        self.assertTrue(self.driver.connected)
        mock_get.assert_called_once()

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.get')
    def test_connect_with_credential_override(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.driver.connect(self.ip, self.port, username="custom_user", password="custom_pass")
        self.assertTrue(result)
        self.assertEqual(self.driver.username, "custom_user")
        self.assertEqual(self.driver.password, "custom_pass")
        self.assertEqual(self.driver.auth.username, "custom_user")
        self.assertEqual(self.driver.auth.password, "custom_pass")

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.get')
    def test_connect_without_override_keeps_default_credentials(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.driver.connect(self.ip, self.port)
        self.assertEqual(self.driver.username, "admin")
        self.assertEqual(self.driver.password, "admin")

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.put')
    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.WtiVmrHd4d20Driver.get_channel_count', return_value=20)
    def test_turn_on(self, mock_count, mock_put):
        self.driver.connected = True
        self.driver.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "OK_RAW"
        mock_put.return_value = mock_response

        response = self.driver.turn_on(1)
        self.assertTrue(response.success)
        self.assertEqual(response.raw, "OK_RAW")
        self.assertEqual(response.action, "turn_on")
        self.assertEqual(response.channel, 1)
        mock_put.assert_called_once_with(
            f"http://{self.ip}:{self.port}/api/v2/plugs/1",
            json={"action": 1},
            auth=self.driver.auth,
            timeout=self.driver.timeout
        )

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.get')
    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.WtiVmrHd4d20Driver.get_channel_count', return_value=20)
    def test_get_status_on(self, mock_count, mock_get):
        self.driver.connected = True
        self.driver.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": 1}
        mock_response.text = '{"status": 1}'
        mock_get.return_value = mock_response

        response = self.driver.get_status(2)
        self.assertEqual(response.status, "ON")
        self.assertEqual(response.raw, '{"status": 1}')
        self.assertTrue(response.success)
        self.assertEqual(response.channel, 2)

    def test_get_model(self):
        self.assertEqual(self.driver.get_model(), "WTI VMR-HD4D20 C19")

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.get')
    def test_get_channel_count_from_device(self, mock_get):
        self.driver.connected = True
        self.driver.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": i} for i in range(1, 9)]
        mock_get.return_value = mock_response

        self.assertEqual(self.driver.get_channel_count(), 8)

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.get')
    def test_get_channel_count_falls_back_on_error(self, mock_get):
        self.driver.connected = True
        self.driver.base_url = f"http://{self.ip}:{self.port}/api/v2"
        mock_get.side_effect = requests.exceptions.ConnectionError("unreachable")

        self.assertEqual(self.driver.get_channel_count(), WtiVmrHd4d20Driver.DEFAULT_CHANNEL_COUNT)

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.WtiVmrHd4d20Driver.get_channel_count', return_value=20)
    def test_out_of_range_channel_raises_value_error(self, mock_count):
        self.driver.connected = True
        self.driver.base_url = f"http://{self.ip}:{self.port}/api/v2"

        with self.assertRaises(ValueError) as ctx:
            self.driver.turn_on(0)
        self.assertIn("out of range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.driver.turn_off(21)
        self.assertIn("out of range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.driver.get_status(-1)
        self.assertIn("out of range", str(ctx.exception))



if __name__ == '__main__':
    unittest.main()
