from enum import Enum 
class Command(Enum):
    START_RECORDING = 1
    END_RECORDING = 2
    GET_RECORDING = 3
    CAPTURE_IMAGE = 4
    START_LIVE = 5
    END_LIVE = 6
    EXIT = 7
    
class Message:
    TYPE_ERROR = "Error"
    TYPE_MESSAGE = "Message"
    TYPE_DATA = "data"

    DATA_IMAGE = {
        "left_img":None,
        "right_img":None
    }

    def __init__(self,type,data=None,error=None,message=None):
        self.type = type    
        self.data = data
        self.message = message
        self.error = error

    def __str__(self):
        return f"Type : {self.type}, Data : {self.data}, Error : {self.error}"
    
class Request:
    def __init__(self,got_size=0,
                 start_recording=False,
                 capture_img=False,
                 end_recording=False,
                 get_recording=False,
                 exit_=False,
                 start_live=False,
                 end_live=False):
        self.got_size = got_size    
        self.start_recording = start_recording
        self.capture_img = capture_img
        self.end_recording = end_recording
        self.get_recording = get_recording
        self.exit = exit_
        self.start_live = start_live
        self.end_live = end_live

    def __str__(self):
        return f"got_size : {self.got_size},\
        start_recording : {self.start_recording},\
        start_recording : {self.start_recording},\
        capture_img : {self.capture_img},\
        end_recording : {self.end_recording},\
        get_recording : {self.get_recording},\
        exit : {self.exit},\
        start_live : {self.start_live},\
        end_live : {self.end_live}"