import os
import cv2
import time
import logging
from utils.socket_handler import SocketHandler
from utils.command_handler import Request,Response,Command,FrameData,CameraConfig
import argparse
import numpy as np
from config.settings import HOST,PORT_C,PORT_S,HEADER_SIZE,RECORDING_DIR





def stero_video_writer(callback,left_file_name,right_file_name):
    recording_dir = os.path.join(os.path.dirname(__file__),RECORDING_DIR)

    config:CameraConfig = callback()

    frame_count = config.frame_count
    fps=config.fps
    width=config.width
    height=config.height
    bar_length = 30
    count = 0

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID') 
    out_l = cv2.VideoWriter(left_file_name, fourcc, fps, (width, height))
    out_r = cv2.VideoWriter(right_file_name, fourcc, fps, (width, height))

    while True:
        data:FrameData = callback()

        if data.header.end:
            break

        # Decode buffer
        frame_l = cv2.imdecode(np.frombuffer(data.data.left, np.uint8), cv2.IMREAD_COLOR)
        frame_r = cv2.imdecode(np.frombuffer(data.data.right, np.uint8), cv2.IMREAD_COLOR)

        progress = count / frame_count
        filled = int(bar_length * progress)
        bar = '*' * filled + '-' * (bar_length - filled)
        print(f'\rDownloading... |{bar}| {int(progress*100)}%', end='')

        # Write the frame to file
        out_l.write(frame_l)  
        out_r.write(frame_r)
        count+=1
        # cv2.waitKey(1)  # simulate ~30fps
    
    print('\rDownloading... |' + '*' * bar_length + '| 100%')
    print("Downloading Complete!")

    out_l.release()
    out_r.release()

    return left_file_name,right_file_name

# if DEBUG:
#     logging.basicConfig(filename="app_c.log", level=logging.DEBUG, 
#                     format="%(asctime)s - %(levelname)s - %(message)s")
# else:
#     logging.basicConfig(filename="app_c.log", level=logging.INFO, 
#                     format="%(asctime)s - %(levelname)s - %(message)s")



class CameraClient:
    """
    Client interface for communicating with a remote stereo camera server over a socket.
    Supports live streaming, image capture, video recording, and retrieval.
    """
    def __init__(self, host=HOST, port_c=PORT_C,port_s=PORT_S, header_size=HEADER_SIZE):
        """
        Initialize CameraClient.

        Args:
            host (str): Server host address.
            port (int): Server port.
            header_size (int): Header size used for socket communication.
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger =  logging.getLogger()
        self.command_socket_handler = SocketHandler(host, port_c)
        self.command_socket_handler.init_reciever()
        self.stream_socket_handler = SocketHandler(host, port_s)
        self.header_size = header_size
        self.count = 0

    def start_recording(self):
        """Send start recording request to the server."""
        try:
            req = Request(Command.START_RECORDING)
            self.command_socket_handler.send(req)
            self.logger.info("Req. sent")
            return self.get_response()
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            return {"error": str(e), "message": None}

    def end_recording(self):
        """Send end recording request to the server."""
        try:
            req = Request(Command.END_RECORDING)
            self.command_socket_handler.send(req)
            return self.get_response()
        except Exception as e:
            self.logger.error(f"Error ending recording: {e}")
            return {"error": str(e), "message": None}

    def get_recording(self):
        """Retrieve recorded video from the server."""
        try:
            req = Request(Command.GET_RECORDING)
            self.command_socket_handler.send(req)

            res = self.get_response(is_file=True)
            if res.error:
                return None, res.error
            
            self.logger.info(res.message)

            def recieve_large_chunks():
                return self.command_socket_handler.recieve(is_file=True)

            return stero_video_writer(recieve_large_chunks,"sl.avi","sr.avi"),None

        except Exception as e:
            self.logger.error(f"Error getting recording: {e}")
            return None, str(e)

    def close(self):
        """Close socket connection."""
        req = Request(Command.EXIT)
        self.command_socket_handler.send(req)
        self.command_socket_handler.close()

    def get_response(self,is_file=False)->Response:
        res = self.command_socket_handler.recieve(is_file=is_file)
        return res

    def start_live(self):
        """Start live video stream from the server."""
        try:
            req = Request(Command.START_LIVE)
            self.command_socket_handler.send(req)
            res = self.get_response()
            if res.error:
                raise Exception(res.error)
            self.logger.info(res.message)
            self.stream_socket_handler.recive_live_stream(self.display_live_capture, separe_thread=True)
        except Exception as e:
            self.logger.error(f"Error starting live stream: {e}")

    def end_live(self):
        """Stop the live video stream."""
        try:
            req = Request(Command.END_LIVE)
            self.command_socket_handler.send(req)
            return self.get_response()
        except Exception as e:
            self.logger.error(f"Error ending live stream: {e}")
            return {"error": str(e), "message": None}

    def capture_image(self):
        """Capture an image from the stereo camera."""
        try:
            req = Request(Command.CAPTURE_IMAGE)
            self.command_socket_handler.send(req)
            res =self.get_response(True)
            if res.error:
                return False, res.error
            self.logger.info(res.message)
            data = res.data
            return True, (data['img_left'], data['img_right'])
        except Exception as e:
            self.logger.error(f"Error capturing image: {e}")
            return False, str(e)

    def display_live_capture(self, status, frames):
        # self.count+=1
        """
        Callback function to display incoming frames in live stream.
        
        Args:
            status (bool): Indicates if a new frame is available.
            frame (np.ndarray): The image frame.
        """
   
        if status:
            cv2.imshow('Live Frame', frames[0])
            cv2.waitKey(1)
            # if (frames is None) or (frames[0] is None): 
            #     return
            # try:
            #     cv2.imshow('Live Frame', frames[0])
            #     cv2.waitKey(1)
            # except Exception as e:
            #     print("<END>" == frames)
            #     with open("out.txt",'w') as f:
            #         f.writelines(frames)
        else:
            cv2.destroyAllWindows()
        # if self.count>50:
        #     self.socket_handler.end_live_stream()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Stereo Camera Client CLI Tool"
    )
    parser.add_argument(
        "--command",
        type=str,
        help="Camera operation to perform",
        choices=[
            "start-recording", "end-recording", "get-recording",
            "start-live", "end-live", "capture-image", "exit"
        ]
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


def main(command,host,port,debug=False,save_logs=False):

    print(host,port)
    
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

    client = CameraClient(host,port,port+1)
   
    try:
        while True:
            res = None
            error = None
            message = None
            if command == "start-recording":
                res = client.start_recording()
            elif command == "end-recording":
                res = client.end_recording()
            elif command == "get-recording":
                video_paths, error = client.get_recording()
                if not error:
                    message = f"[📦 SAVED] Files saved: {video_paths}"
            elif command == "start-live":
                logger.info("[🎥 LIVE] Press 'q' to stop streaming.")
                client.start_live()
            elif command == "end-live":
                res = client.end_live()
            elif command == "capture-image":
                success, result = client.capture_image()
                if success:
                    message="[📸 IMAGE] Image captured successfully."
                else:
                    error=f"[❌ ERROR] {result}"
            elif command == "exit":
                client.close()
                logger.info("[🔌 DISCONNECTED] Client closed.")
                return
            else:
                error="[❓ UNKNOWN COMMAND]"

            if res:
                error = res.error
                message = res.message
            if error:
                logger.info(f"[❌ ERROR] {error}")
            else:
                logger.info(f"[✅ SUCCESS] {message}")
            
            logger.debug("Waiting for command..")
            command = input(">")

    except Exception as e:
        logger.error(f"[⚠️  EXCEPTION] {str(e)}")

    finally:
        client.close()

       




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
    args = parse_args()
    main(args.command,args.host, args.port, args.debug, args.save_logs)
