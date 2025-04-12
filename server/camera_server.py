import threading
import logging
from utils.socket_handler import SocketHandler
from camera.camera import Camera
from utils.command_handler import Command,Message


class CameraServer():
    def __init__(self,socket_handler:SocketHandler,camera:Camera,logger:logging.Logger):
        self.socket_handler = socket_handler
        self.camera = camera
        self.recording_status = False
        self.logger = logger
    
    def handle_request(self,request):
        if request==Command.START_RECORDING:
            if self.recording_status:
                self.socket_handler.send(Message(Message.TYPE_ERROR,error="Alredy recording!"))
                return
            self.recording_status = True
            threading.Thread(target=self.camera.start_recording).start()
            self.socket_handler.send(Message(Message.TYPE_MESSAGE,message="Recording started."))

        elif request == Command.END_RECORDING:
            try:
                if not self.recording_status:
                    self.socket_handler.send(Message(Message.TYPE_ERROR,error="Camera is not recording!"))
                    return

                # End recording
                self.camera.end_recording()
                self.socket_handler.end_live_stream()
                if not self.camera.get_recording_state():
                    self.socket_handler.send(Message(Message.TYPE_MESSAGE,message="Recording ended."))
                    self.recording_status = False
                else:
                    self.socket_handler.send(Message(Message.TYPE_ERROR,error="Something went wrong! Coudn't stop recording."))
            except Exception as e:
                raise e
            
        elif request==Command.CAPTURE_IMAGE:
            img_left,img_right = self.camera.capture_image()
            self.socket_handler.send(Message(Message.TYPE_DATA,data={"left_img":img_left,"right_img":img_right}))

        elif request==Command.GET_RECORDING:
            if self.recording_status:
                self.socket_handler.send(Message(Message.TYPE_ERROR,error="Can't send recording while camera is in recording state! Stop the recording first!"))
            else:
                recordings,error = self.camera.get_recording()
                if error:
                    self.socket_handler.send(Message(Message.TYPE_ERROR,error=error))
                else:
                    self.socket_handler.send(Message(Message.TYPE_DATA,data={"recordings":recordings}))

        elif request==Command.EXIT:
            if self.recording_status:
                self.socket_handler.send(Message(Message.TYPE_ERROR,error="Can't stop camera while camera is in recording state! Stop the recording first!"))
            else:
                self.camera.close()
                self.socket_handler.send(Message(Message.TYPE_MESSAGE,message="Camera closed!"))

        elif request==Command.START_LIVE:
            if not self.camera.is_live_streaming():
                self.socket_handler.send_live_stream(self.camera,separe_thread=True)
            elif self.recording_status:
                self.socket_handler.send(Message(Message.TYPE_ERROR,error="Can't start live streaming while camera is in recording state! Stop the recording first!"))
            else:
                self.socket_handler.send(Message(Message.TYPE_ERROR,error="Already in live streaming!"))

        elif request==Command.END_LIVE:
            if not self.camera.is_live_streaming():
                self.socket_handler.send(Message(Message.TYPE_ERROR,error="Not in live streaming!"))
            else:
                self.camera.stop_live_streaming()
                self.socket_handler.send(Message(Message.TYPE_MESSAGE,message="Live streaming ended."))             
        
        else:
            self.socket_handler.send(Message(Message.TYPE_ERROR,error="Invalid command!"))

    def start(self):
        try:
            while True:
                request = self.socket_handler.recieve()
                if not request:
                    break
                self.handle_request(request)
        except Exception as e:
            self.logger.error(e)
            self.socket_handler.send(Message(Message.TYPE_ERROR,error=f"An error occured! {e}"))
        finally:    
            self.camera.close()
            self.socket_handler.close()

def main():
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

    sh = SocketHandler(HOST,PORT,logger,SocketHandler.TYPE_SERVER)
    camera = Camera(logger)
    cs = CameraServer(sh,camera,logger)
    cs.start()


if __name__ == '__main__':
    main()