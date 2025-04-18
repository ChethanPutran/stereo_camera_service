import logging
from utils.socket_handler import SocketHandler
from camera.camera import Camera
from utils.command_handler import Command, Response,Request,FrameData,CameraConfig,Header
import argparse
import cv2
from config.settings import HOST,PORT_C,PORT_S

def stero_video_reader(callback,left_file_name,right_file_name):
    cap_left = cv2.VideoCapture(left_file_name)
    cap_right = cv2.VideoCapture(right_file_name)

    width = int(cap_left.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_left.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap_left.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap_left.get(cv2.CAP_PROP_FRAME_COUNT))

    # Send video configurations
    callback(CameraConfig(frame_count,fps,width,height))

    while (cap_left.isOpened() and cap_right.isOpened()):
        print("Reading frame...")
        ret1, frame_left = cap_left.read()
        ret2, frame_right = cap_right.read()

        if (not ret1) or (not ret2):
            callback(FrameData(header=Header(end=True)))
            break

        # Encode frame
        _, buffer1 = cv2.imencode('.jpg', frame_left)
        _, buffer2 = cv2.imencode('.jpg', frame_right)
        callback(FrameData(left=buffer1,right=buffer2))
        cv2.waitKey(33)  # simulate ~30fps
    print("Completely sent.")
    cap_left.release()
    cap_right.release()

class CameraServer:
    """
    Server class to handle camera commands over a socket.
    Supports stereo vision camera operations like recording,
    live streaming, capturing images, etc.
    """

    def __init__(self,host=HOST,port_c=PORT_C,port_s=PORT_S):
        """
        Initialize the server with a socket handler and camera.
        """
        self.command_socket_handler = SocketHandler(host,port_c,type=SocketHandler.TYPE_SERVER)
        self.command_socket_handler.init_reciever()
        self.stream_socket_handler = SocketHandler(host,port_s,type=SocketHandler.TYPE_SERVER)
        self.camera = Camera()
        self.recording_status = False
        self.logger = logging.getLogger()

    def start(self):
        pass

    def get_request(self)->Request:
        res = self.command_socket_handler.recieve()
        return res

    def handle_command(self, command):
        """
        Handle incoming requests from the client.
        Routes the request to appropriate camera operation.
        """
        try:
            self.logger.info("Got command :"+str(command))
            if command == Command.START_RECORDING:
                if self.camera.is_recording():
                    self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="Already recording!"))
                    return
                self.logger.info("Starting recording...")
                self.camera.start_recording()
                self.logger.info("Recording started.")
                self.command_socket_handler.send(Response(Response.TYPE_MESSAGE, message="Recording started."))

            elif command == Command.END_RECORDING:
                if not self.camera.is_recording():
                    self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="Camera is not recording!"))
                    return

                self.camera.end_recording()
                if not self.camera.is_recording():
                    self.command_socket_handler.send(Response(Response.TYPE_MESSAGE, message="Recording ended."))
                    self.recording_status = False
                else:
                    self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="Couldn't stop recording."))

            elif command == Command.CAPTURE_IMAGE:
                img_left, img_right = self.camera.capture_image()
                self.command_socket_handler.send(Response(Response.TYPE_DATA, data={"left_img": img_left, "right_img": img_right}))

            elif command == Command.GET_RECORDING:
                if self.camera.is_recording():
                    self.command_socket_handler.send(Response(
                        Response.TYPE_ERROR,
                        error="Can't send recording while camera is recording! Stop the recording first!"
                    ))
                    return
                self.logger.debug("Fetching recording...")

                rec_file_name = self.camera.get_recorded_file()
                if not rec_file_name[0]:
                    self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="No recording exists!")) 
                    return

                self.command_socket_handler.send(Response(Response.TYPE_MESSAGE, message="Sending recording...")) 
                stero_video_reader(self.command_socket_handler.send,*rec_file_name)
                self.camera.clear_recordings()

            elif command == Command.EXIT:
                if self.camera.is_recording():
                    self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="Stop recording before exiting."))
                    return

                self.camera.close()
                return
                # self.command_socket_handler.send(Response(Response.TYPE_MESSAGE, message="Camera closed!"))

            elif command == Command.START_LIVE:
                if self.camera.is_recording():
                    self.command_socket_handler.send(Response(
                        Response.TYPE_ERROR,
                        error="Can't start live streaming while recording!"
                    ))
                elif not self.camera.is_live_streaming():
                    self.camera.start_live_streaming()
                    self.command_socket_handler.send(Response(Response.TYPE_MESSAGE, message="Live streaming started."))
                    self.stream_socket_handler.send_live_stream(self.camera, separe_thread=True)
                else:
                    self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="Already live streaming."))

            elif command == Command.END_LIVE:
                if not self.camera.is_live_streaming():
                    self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="Not in live streaming!"))
                else:
                    self.camera.stop_live_streaming()
                    self.command_socket_handler.send(Response(Response.TYPE_MESSAGE, message="Live streaming ended."))

            else:
                self.command_socket_handler.send(Response(Response.TYPE_ERROR, error="Invalid command!"))

        except Exception as e:
            self.camera.close()
            self.logger.exception("Exception while handling request")
            self.command_socket_handler.send(Response(Response.TYPE_ERROR, error=f"Internal server error: {str(e)}"))

    def start(self):
        """
        Start listening for client requests.
        """
        try:
            while True:
                request = self.get_request()
                self.logger.debug("New Req: "+str(request))
                if request:
                    self.handle_command(request.command)
        except Exception as e:
            # self.logger.exception("Error in server loop")
            self.command_socket_handler.send(Response(Response.TYPE_ERROR, error=f"An error occurred: {str(e)}"))
        finally:
            self.camera.close()
            self.command_socket_handler.close()

def parse_args():
    parser = argparse.ArgumentParser(
        description="Stereo Camera Server CLI Tool"
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host name (default: 'raspberrypi.local')",
        default="raspberrypi.local"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port (default: 8000)",
        default=8000
    )
    parser.add_argument(
        "--debug",
        type=int,
        help="Enable debug mode (default: 0 for off)",
        choices=[0, 1],
        default=0
    )
    parser.add_argument(
        "--save_logs",
        type=int,
        help="Save logs to file (default: 0 for off)",
        choices=[0, 1],
        default=0
    )

    return parser.parse_args()

def main(host='raspberrypi.local',port=8000,debug=False,save_logs=False):
    """
    Entry point for the Camera Server.
    Initializes logging, camera, socket handler, and starts server.
    """


    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)

    if save_logs:
        handler = logging.FileHandler('app_s.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    cs = CameraServer(host, port_c=port, port_s=port+1)
    cs.start()



if __name__ == '__main__':
    args = parse_args()
    main(args.host, args.port, args.debug, args.save_logs)
