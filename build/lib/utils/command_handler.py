from enum import Enum

class Serializer:
    def to_dict(self): 
        pass
class DeSerializer:
    def from_dict(self): 
        pass 
class Command(Enum):
    """
    Enum representing different types of commands used for controlling a system,
    such as recording, capturing images, live streaming, and exiting.
    """
    START_RECORDING = 1
    END_RECORDING = 2
    GET_RECORDING = 3
    CAPTURE_IMAGE = 4
    START_LIVE = 5
    END_LIVE = 6
    EXIT = 7

class Response(Serializer,DeSerializer):
    """
    A class to represent a message object used for structured communication.

    Attributes:
        type (str): Type of message (Error, Message, or data).
        data (any): The payload or content of the message.
        error (str): Error message, if any.
        message (str): Human-readable message content.
    """

    TYPE_ERROR = "Error"
    TYPE_MESSAGE = "Message"
    TYPE_DATA = "data"

    # Template for holding stereo image data
    DATA_IMAGE = {
        "left_img": None,
        "right_img": None
    }

    def __init__(self, type, data=None, error=None, message=None):
        """
        Initializes a Message object.

        Args:
            type (str): Type of the message (use TYPE_* constants).
            data (any, optional): The payload.
            error (str, optional): Error string, if the message is an error.
            message (str, optional): A general message.
        """
        self.type = type    
        self.data = data
        self.message = message
        self.error = error

    def __str__(self):
        """
        Returns a string representation of the message object.
        """
        return f"Type : {self.type}, Data : {self.data}, Error : {self.error}"

    def to_dict(self):
        """
        Converts the message object into a dictionary.

        Returns:
            dict: A dictionary representation of the message.
        """
        return {
            "type": self.type,
            "data": self.data,
            "error": self.error,
            "message": self.message
        }

    @classmethod
    def from_dict(cls, data):
        """
        Creates a Message object from a dictionary.

        Args:
            data (dict): Dictionary with keys matching message attributes.

        Returns:
            Message: An instance of Message.
        """
        return cls(type=data['type'], data=data.get('data'), error=data.get('error'), message=data.get('message'))

class Request(Serializer,DeSerializer):
    """
    A class representing a set of request flags used for communication between components.

    Attributes:
        got_size (int): Size of the received data (useful for files).
        start_recording (bool): True if the system should start recording.
        capture_img (bool): True if an image should be captured.
        end_recording (bool): True if the recording should end.
        get_recording (bool): True if the recorded data should be fetched.
        exit (bool): True if the session should be terminated.
        start_live (bool): True if live streaming should begin.
        end_live (bool): True if live streaming should end.
    """

    def __init__(self, command):
        """
        Initializes a Request object with the given flags.

        Args:
            command (int)
        """
        self.command = command 

    def __str__(self):
        """
        Returns a string representation of the request state.
        """
        return f"command :{self.command}"

    def to_dict(self):
        """
        Serializes the Request object into a dictionary.

        Returns:
            dict: Dictionary containing all request fields.
        """
        return {
            "command": self.command
        }

    @classmethod
    def from_dict(cls, data):
        """
        Deserializes a dictionary into a Request object.

        Args:
            data (dict): Dictionary containing request fields.

        Returns:
            Request: An instance of the Request class.
        """
        return cls(
            command=data.get("command", 0)
        )

class Header(Serializer,DeSerializer):
    def __init__(self,start=True,end=False,configs=None):
        self.start=start
        self.end=end
        self.configs=configs
    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "configs": self.configs.to_dict() if self.configs else None
        }
    def from_dict(cls, data):
        return cls(start=data['start'], end=data.get('end'))

class Frame(Serializer,DeSerializer):
    def __init__(self,left,right):
        self.right = right
        self.left = left
    def to_dict(self):
        return {
            "left": self.left,
            "right": self.right,
        }
    def from_dict(cls, data):
        return cls(left=data['left'], right=data.get('right'))

class FrameData(Serializer,DeSerializer):
    def __init__(self,left=None,right=None,header=None):
        self.header = header or Header(False,False)
        self.data = Frame(left,right)
        
    def __str__(self):
        return f"header : {self.header.to_dict()}, data : {self.data.to_dict()}"

    def to_dict(self):
        return {
            "header": self.header.to_dict(),
            "data": self.data.to_dict()
        }

    @classmethod
    def from_dict(cls, data):
        return cls(header=data['header'], data=data.get('data'))
  
class CameraConfig(Serializer,DeSerializer):
    FPS = 30
    WIDTH = 720
    HEIGHT = 720

    def __init__(self,frame_count,fps=FPS,width=WIDTH,height=HEIGHT):
        self.fps=fps
        self.width=width
        self.height=height
        self.frame_count=frame_count

    def __str__(self):
        """
        Returns a string representation of the camera configurations.
        """
        return f"FPS : {self.fps}, WIDTH : {self.WIDTH}, HEIGHT : {self.HEIGHT}, frame_count :{self.frame_count}"

    def to_dict(self):
        """
        Converts the CameraConfig object into a dictionary.

        Returns:
            dict: A dictionary representation of the CameraConfig.
        """
        return {
            "fps": self.FPS,
            "width": self.WIDTH,
            "height": self.HEIGHT,
            "frame_count": self.frame_count,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Creates a CameraConfig object from a dictionary.

        Args:
            data (dict): Dictionary with keys matching CameraConfig attributes.

        Returns:
            CameraConfig: An instance of CameraConfig.
        """
        return cls(frame_count=data.get('frame_count'),fps=data['fps'], width=data.get('width'), height=data.get('height'))

