import threading
import logging
from utils.socket_handler import SocketHandler
from camera.camera import Camera
from utils.command_handler import Command, Message

class CameraServer:
    """
    Server class to handle camera commands over a socket.
    Supports stereo vision camera operations like recording,
    live streaming, capturing images, etc.
    """

    def __init__(self, socket_handler: SocketHandler, camera: Camera, logger: logging.Logger):
        """
        Initialize the server with a socket handler and camera.
        """
        self.socket_handler = socket_handler
        self.camera = camera
        self.recording_status = False
        self.logger = logger

    def handle_request(self, request):
        """
        Handle incoming requests from the client.
        Routes the request to appropriate camera operation.
        """
        try:
            if request == Command.START_RECORDING:
                if self.recording_status:
                    self.socket_handler.send(Message(Message.TYPE_ERROR, error="Already recording!"))
                    return
                self.recording_status = True
                threading.Thread(target=self.camera.start_recording).start()
                self.socket_handler.send(Message(Message.TYPE_MESSAGE, message="Recording started."))

            elif request == Command.END_RECORDING:
                if not self.recording_status:
                    self.socket_handler.send(Message(Message.TYPE_ERROR, error="Camera is not recording!"))
                    return

                self.camera.end_recording()
                self.socket_handler.end_live_stream()

                if not self.camera.get_recording_state():
                    self.socket_handler.send(Message(Message.TYPE_MESSAGE, message="Recording ended."))
                    self.recording_status = False
                else:
                    self.socket_handler.send(Message(Message.TYPE_ERROR, error="Couldn't stop recording."))

            elif request == Command.CAPTURE_IMAGE:
                img_left, img_right = self.camera.capture_image()
                self.socket_handler.send(Message(Message.TYPE_DATA, data={"left_img": img_left, "right_img": img_right}))

            elif request == Command.GET_RECORDING:
                if self.recording_status:
                    self.socket_handler.send(Message(
                        Message.TYPE_ERROR,
                        error="Can't send recording while camera is recording! Stop the recording first!"
                    ))
                    return

                recordings, error = self.camera.get_recording()
                if error:
                    self.socket_handler.send(Message(Message.TYPE_ERROR, error=error))
                else:
                    self.socket_handler.send(Message(Message.TYPE_DATA, data={"recordings": recordings}))

            elif request == Command.EXIT:
                if self.recording_status:
                    self.socket_handler.send(Message(Message.TYPE_ERROR, error="Stop recording before exiting."))
                    return

                self.camera.close()
                self.socket_handler.send(Message(Message.TYPE_MESSAGE, message="Camera closed!"))

            elif request == Command.START_LIVE:
                if self.recording_status:
                    self.socket_handler.send(Message(
                        Message.TYPE_ERROR,
                        error="Can't start live streaming while recording!"
                    ))
                elif not self.camera.is_live_streaming():
                    self.socket_handler.send_live_stream(self.camera, separe_thread=True)
                else:
                    self.socket_handler.send(Message(Message.TYPE_ERROR, error="Already live streaming."))

            elif request == Command.END_LIVE:
                if not self.camera.is_live_streaming():
                    self.socket_handler.send(Message(Message.TYPE_ERROR, error="Not in live streaming!"))
                else:
                    self.camera.stop_live_streaming()
                    self.socket_handler.send(Message(Message.TYPE_MESSAGE, message="Live streaming ended."))

            else:
                self.socket_handler.send(Message(Message.TYPE_ERROR, error="Invalid command!"))

        except Exception as e:
            self.logger.exception("Exception while handling request")
            self.socket_handler.send(Message(Message.TYPE_ERROR, error=f"Internal server error: {str(e)}"))

    def start(self):
        """
        Start listening for client requests.
        """
        try:
            while True:
                request = self.socket_handler.recieve()
                if not request:
                    break
                self.handle_request(request)
        except Exception as e:
            self.logger.exception("Error in server loop")
            self.socket_handler.send(Message(Message.TYPE_ERROR, error=f"An error occurred: {str(e)}"))
        finally:
            self.camera.close()
            self.socket_handler.close()

def main():
    """
    Entry point for the Camera Server.
    Initializes logging, camera, socket handler, and starts server.
    """
    STERIO = True
    DEBUG = True
    HEADER_SIZE = 10
    HOST = 'raspberrypi.local'
    PORT = 8000
    SAVE_LOGS = False

    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)

    if SAVE_LOGS:
        handler = logging.FileHandler('app_s.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    sh = SocketHandler(HOST, PORT, logger, SocketHandler.TYPE_SERVER)
    camera = Camera(logger)
    cs = CameraServer(sh, camera, logger)
    cs.start()

if __name__ == '__main__':
    main()
