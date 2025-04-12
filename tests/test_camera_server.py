import unittest
from unittest.mock import MagicMock
from server.camera_server import CameraServer
from utils.command_handler import Command


class TestCameraServer(unittest.TestCase):

    def setUp(self):
        self.mock_socket = MagicMock()
        self.mock_camera = MagicMock()
        self.logger = MagicMock()
        self.server = CameraServer(self.mock_socket, self.mock_camera, self.logger)

    def test_handle_start_recording(self):
        self.server.handle_request(Command.START_RECORDING)
        self.assertTrue(self.server.recording_status)
        self.mock_socket.send.assert_called()

    def test_handle_end_recording(self):
        self.server.recording_status = True
        self.mock_camera.get_recording_state.return_value = False
        self.server.handle_request(Command.END_RECORDING)
        self.assertFalse(self.server.recording_status)
        self.mock_socket.send.assert_called()

    def test_handle_invalid_command(self):
        self.server.handle_request("INVALID")
        self.mock_socket.send.assert_called()


if __name__ == '__main__':
    unittest.main()
