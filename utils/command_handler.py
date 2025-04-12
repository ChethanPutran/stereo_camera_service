from enum import Enum

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


class Message:
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


class Request:
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

    def __init__(self, got_size=0,
                 start_recording=False,
                 capture_img=False,
                 end_recording=False,
                 get_recording=False,
                 exit_=False,
                 start_live=False,
                 end_live=False):
        """
        Initializes a Request object with the given flags.

        Args:
            got_size (int): Received file size.
            start_recording (bool): Flag to start recording.
            capture_img (bool): Flag to capture an image.
            end_recording (bool): Flag to end recording.
            get_recording (bool): Flag to request the recorded file.
            exit_ (bool): Flag to exit the session.
            start_live (bool): Flag to start live streaming.
            end_live (bool): Flag to stop live streaming.
        """
        self.got_size = got_size    
        self.start_recording = start_recording
        self.capture_img = capture_img
        self.end_recording = end_recording
        self.get_recording = get_recording
        self.exit = exit_
        self.start_live = start_live
        self.end_live = end_live

    def __str__(self):
        """
        Returns a string representation of the request state.
        """
        return f"got_size : {self.got_size},\
        start_recording : {self.start_recording},\
        capture_img : {self.capture_img},\
        end_recording : {self.end_recording},\
        get_recording : {self.get_recording},\
        exit : {self.exit},\
        start_live : {self.start_live},\
        end_live : {self.end_live}"

    def to_dict(self):
        """
        Serializes the Request object into a dictionary.

        Returns:
            dict: Dictionary containing all request fields.
        """
        return {
            "got_size": self.got_size,
            "start_recording": self.start_recording,
            "capture_img": self.capture_img,
            "end_recording": self.end_recording,
            "get_recording": self.get_recording,
            "exit": self.exit,
            "start_live": self.start_live,
            "end_live": self.end_live
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
            got_size=data.get("got_size", 0),
            start_recording=data.get("start_recording", False),
            capture_img=data.get("capture_img", False),
            end_recording=data.get("end_recording", False),
            get_recording=data.get("get_recording", False),
            exit_=data.get("exit", False),
            start_live=data.get("start_live", False),
            end_live=data.get("end_live", False)
        )
