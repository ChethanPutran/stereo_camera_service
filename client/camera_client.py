import sys
import os
import cv2
import time
import logging
from utils.socket_handler import SocketHandler
from utils.command_handler import Request
import argparse

STERIO = True
RECORDING_DIR = 'recordings'
DEBUG = True
HOST = 'raspberrypi.local'
PORT = 8000
HEADER_SIZE = 10

def extract_video(recording,sterio=STERIO):
    recording_dir = os.path.join(os.path.dirname(__file__),RECORDING_DIR)

    fname_l = os.path.join(recording_dir,recording[0][0])
    buff_l = recording[0][1]

    with open(fname_l,'wb') as file:
        file.write(buff_l)

    if sterio:
        fname_r = os.path.join(recording_dir,recording[1][0])
        buff_r = recording[1][1]

        with open(fname_r,'wb') as file:
            file.write(buff_r)
        return fname_l,fname_r
    
    return fname_l

# if DEBUG:
#     logging.basicConfig(filename="app_c.log", level=logging.DEBUG, 
#                     format="%(asctime)s - %(levelname)s - %(message)s")
# else:
#     logging.basicConfig(filename="app_c.log", level=logging.INFO, 
#                     format="%(asctime)s - %(levelname)s - %(message)s")
logging.basicConfig(level=logging.DEBUG)


class CameraClient:
    """
    Client interface for communicating with a remote stereo camera server over a socket.
    Supports live streaming, image capture, video recording, and retrieval.
    """
    def __init__(self, host=HOST, port=PORT, header_size=HEADER_SIZE, logger=None):
        """
        Initialize CameraClient.

        Args:
            host (str): Server host address.
            port (int): Server port.
            header_size (int): Header size used for socket communication.
            logger (logging.Logger, optional): Logger instance.
        """
        self.host = host
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self.socket_handler = SocketHandler(host, port, logger=self.logger)
        self.header_size = header_size
        self.live_ended = False

    def start_recording(self):
        """Send start recording request to the server."""
        try:
            req = Request(start_recording=True)
            self.socket_handler.send(req)
            return self.socket_handler.recieve()
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            return {"error": str(e), "message": None}

    def end_recording(self):
        """Send end recording request to the server."""
        try:
            req = Request(end_recording=True)
            self.socket_handler.send(req)
            return self.socket_handler.recieve()
        except Exception as e:
            self.logger.error(f"Error ending recording: {e}")
            return {"error": str(e), "message": None}

    def get_recording(self):
        """Retrieve recorded video from the server."""
        try:
            req = Request(get_recording=True)
            self.socket_handler.send(req)
            res = self.socket_handler.recieve(is_file=True)
            if res['error']:
                return None, res['error']
            print(res['message'])
            return extract_video(res['data']), None
        except Exception as e:
            self.logger.error(f"Error getting recording: {e}")
            return None, str(e)

    def close(self):
        """Close socket connection."""
        self.socket_handler.close()

    def start_live(self):
        """Start live video stream from the server."""
        try:
            req = Request(start_live=True)
            self.socket_handler.send(req)
            self.socket_handler.recive_live_stream(self.display_live_capture, separe_thread=True)
        except Exception as e:
            self.logger.error(f"Error starting live stream: {e}")

    def end_live(self):
        """Stop the live video stream."""
        try:
            req = Request(end_live=True)
            self.socket_handler.send(req)
            # Wait for confirmation
            animation = "|/-\\"
            idx = 0
            while not self.live_ended:
                print(animation[idx % len(animation)], end="\r")
                idx += 1
                time.sleep(0.1)
            return self.socket_handler.recieve()
        except Exception as e:
            self.logger.error(f"Error ending live stream: {e}")
            return {"error": str(e), "message": None}

    def capture_image(self):
        """Capture an image from the stereo camera."""
        try:
            req = Request(capture_img=True)
            self.socket_handler.send(req)
            res = self.socket_handler.recieve(is_file=True)
            if res['error']:
                return False, res['error']
            print(res['message'])
            data = res['data']
            return True, (data['img_left'], data['img_right'])
        except Exception as e:
            self.logger.error(f"Error capturing image: {e}")
            return False, str(e)

    def display_live_capture(self, status, frame):
        """
        Callback function to display incoming frames in live stream.
        
        Args:
            status (bool): Indicates if a new frame is available.
            frame (np.ndarray): The image frame.
        """
        if status and frame is not None:
            cv2.imshow('Live Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.socket_handler.end_live_stream()
        else:
            self.live_ended = True
        cv2.destroyAllWindows()

           
def run_camera_client_command(command):
    client = CameraClient()
    try:
        if command == "start-recording":
            res = client.start_recording()
        elif command == "end-recording":
            res = client.end_recording()
        elif command == "get-recording":
            video_paths, error = client.get_recording()
            if error:
                print(f"[❌ ERROR] {error}")
            else:
                print(f"[📦 SAVED] Files saved: {video_paths}")
            return
        elif command == "start-live":
            print("[🎥 LIVE] Press 'q' to stop streaming.")
            client.start_live()
            return
        elif command == "end-live":
            res = client.end_live()
        elif command == "capture-image":
            success, result = client.capture_image()
            if success:
                print("[📸 IMAGE] Image captured successfully.")
            else:
                print(f"[❌ ERROR] {result}")
            return
        elif command == "exit":
            client.close()
            print("[🔌 DISCONNECTED] Client closed.")
            sys.exit(0)
        else:
            print("[❓ UNKNOWN COMMAND]")
            return

        if res["error"]:
            print(f"[❌ ERROR] {res['error']}")
        else:
            print(f"[✅ SUCCESS] {res['message']}")

    except Exception as e:
        print(f"[⚠️  EXCEPTION] {str(e)}")

    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Stereo Camera Client CLI Tool"
    )
    parser.add_argument(
        "command",
        type=str,
        help="Camera operation to perform",
        choices=[
            "start-recording", "end-recording", "get-recording",
            "start-live", "end-live", "capture-image", "exit"
        ]
    )

    args = parser.parse_args()
    run_camera_client_command(args.command)


def test_live_stream():
    # Testing
    try:
        client = CameraClient()
        client.start_live()
    except Exception as e:
        print(e)
    finally:
        client.close()


def test_recording():
    client = None
    try:
        client = CameraClient()
        res = client.start_recording()
        time.sleep(10)
        print(res)
        res = client.end_recording()    
        print(res)
        res = client.get_recording()    
        print(res)
    except Exception as e:
        print(e)
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
