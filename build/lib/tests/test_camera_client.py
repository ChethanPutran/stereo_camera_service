import unittest
from unittest.mock import MagicMock, patch
from client.camera_client import CameraClient


class TestCameraClient(unittest.TestCase):

    @patch('camera_client.SocketHandler')
    def test_start_recording_success(self, MockSocketHandler):
        mock_socket = MockSocketHandler.return_value
        mock_socket.recieve.return_value = {'error': None, 'message': 'Started'}

        client = CameraClient()
        res = client.start_recording()
        self.assertEqual(res['message'], 'Started')

    @patch('camera_client.SocketHandler')
    def test_get_recording_failure(self, MockSocketHandler):
        mock_socket = MockSocketHandler.return_value
        mock_socket.recieve.return_value = {'error': 'No recording', 'message': '', 'data': None}

        client = CameraClient()
        result, error = client.get_recording()
        self.assertIsNone(result)
        self.assertEqual(error, 'No recording')

    @patch('camera_client.SocketHandler')
    def test_capture_image(self, MockSocketHandler):
        mock_socket = MockSocketHandler.return_value
        mock_socket.recieve.return_value = {
            'error': None,
            'message': 'Captured',
            'data': {'img_left': b'123', 'img_right': b'456'}
        }

        client = CameraClient()
        success, imgs = client.capture_image()
        self.assertTrue(success)
        self.assertIn('img_left', imgs)
        self.assertIn('img_right', imgs)


if __name__ == '__main__':
    unittest.main()
