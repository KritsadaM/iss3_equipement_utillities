import unittest
from unittest.mock import patch, MagicMock
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

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.put')
    def test_turn_on(self, mock_put):
        self.driver.connected = True
        self.driver.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "OK_RAW"
        mock_put.return_value = mock_response

        result, raw = self.driver.turn_on(1)
        self.assertTrue(result)
        self.assertEqual(raw, "OK_RAW")
        mock_put.assert_called_once_with(
            f"http://{self.ip}:{self.port}/api/v2/plugs/1",
            json={"action": 1},
            auth=self.driver.auth,
            timeout=self.driver.timeout
        )

    @patch('equipment_drivers.pdu.wti_vmr_hd4d20.requests.Session.get')
    def test_get_status_on(self, mock_get):
        self.driver.connected = True
        self.driver.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": 1}
        mock_response.text = '{"status": 1}'
        mock_get.return_value = mock_response

        status, raw = self.driver.get_status(2)
        self.assertEqual(status, "ON")
        self.assertEqual(raw, '{"status": 1}')

    def test_get_model(self):
        self.assertEqual(self.driver.get_model(), "WTI VMR-HD4D20 C19")

if __name__ == '__main__':
    unittest.main()
