import os
import cv2
import time
import logging
from utils.socket_handler import SocketHandler
from utils.command_handler import Request

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
    def __init__(self,host=HOST,port=PORT,header_size=HEADER_SIZE,logger=None):
        self.host = host
        self.port = port
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
        self.socket_handler = SocketHandler(host,port,logger=self.logger)
        self.header_size = header_size
        self.live_ended = False

    def start_recording(self):
        req = Request(start_recording=True)
        self.socket_handler.send(req)
        res = self.socket_handler.recieve()
        return res

    def end_recording(self):
        req = Request(end_recording=True)
        self.socket_handler.send(req)
        res = self.socket_handler.recieve()
        return res

    def get_recording(self):
        req = Request(get_recording=True)
        self.socket_handler.send(req)
        res = self.socket_handler.recieve(is_file=True)
        if res['error']:
            return None,res['error']
        else:
            print(res['message'])
        
        return extract_video(res['data']),None

    def close(self):
        self.socket_handler.close()

    def start_live(self):
        req = Request(start_live=True)
        self.socket_handler.send(req)
        self.socket_handler.recive_live_stream(self.display_live_capture,separe_thread=True)

    def end_live(self):
        self.send(end_live=True)
        animation = "|/-\\"
        idx = 0
        while not self.live_ended:
            print(animation[idx % len(animation)], end="\r")
            idx += 1
            time.sleep(0.1)

        res = self.recieve()
        return res
    
    def capture_image(self):
        img_left,img_right = None,None

        req = Request(capture_img=True)
        self.socket_handler.send(req)
        res = self.socket_handler.recieve(is_file=True)
        res = res['data']

        if res['error']:
            return False,res['error']
        
        print(res['message'])
        img_left = res['data']['img_left']
        img_right = res['data']['img_right']

        return True, (img_left,img_right)

    def display_live_capture(self,status,frame):
        if status:
            cv2.imshow('frame',frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.socket_handler.end_live_stream()

        cv2.destroyAllWindows()
           
def main():
    

    camera_client = CameraClient()

    print("*"*50)
    print("1 - Start recording \n\
        2 - End recording \n\
        3 - Get recording \n\
        4 - Start Live streaming \n\
        5 - End Live streaming \n\
        6 - Capture photo \n\
        7 - Exit \n\
        ")

    try:
        while True:
            command = int(input(">"))

            if(command==1):
                res = camera_client.start_recording()
                if res['error']:
                    print(res["error"]) 
                else:
                    print(res["message"])
            elif(command==2):
                res = camera_client.end_recording()
                if res['error']:
                    print(res["error"])
                else:
                    print(res["message"])
            elif(command==3):
                recording,error= camera_client.get_recording()
                if  error:
                    print(error)
                else:
                    print("Received recording :",recording)
            elif(command==4):
                camera_client.start_live()
                print("Live started...")
            elif(command==5):
                res = camera_client.end_live()
                if res["error"]:
                    print(res["error"])
                else:
                    print(res["message"])
            elif(command==5):
                res = camera_client.capture_image()
                if res["error"]:
                    print(res["error"])
                else:
                    print(res["message"])
            elif(command==7):
                res = camera_client.exit()
                if res['error']:
                    print(res['error'])
                else:
                    print(res["message"])
                    break
    except Exception as e:
        print(e)
    camera_client.close()  # close the connection


def display_frame(status,frame):
    if status:
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True
    return False


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
if __name__ == '__main__':
    test_recording()
    # Start recording

    # End Recording
    # Get recording
    # Start live stream
    # End live stream
    # Capture photo
    # Exit
