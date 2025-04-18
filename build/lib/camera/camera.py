import cv2
import time
import numpy as np
from utils.socket_handler import Streamer

try:
    from picamera2 import Picamera2
except Exception as e:
    class Picamera2:
        cap = cv2.VideoCapture(0)
        def __init__(self,id):
            self.id = id
        def create_video_configuration(self,main,controls):
            return None
        def configure(self,config):
            pass
        def capture_array(self):
            return self.cap.read()[1]
        def read(self):
            return self.cap.read()[1]
        def start(self):
            pass
        def stop(self):
            pass
        def close(self):
            return self.cap.release()


class CameraInterface:
    """
    An abstract class defining the interface for a Camera.
    This should be extended to implement actual camera functionality.
    """
    pass

class Camera(Streamer):
    """ 
    Camera class for managing stereo vision using two cameras (left and right).
    Provides functionality for capturing images, live streaming, recording, and processing images.

    Calibration parameters:
        f - focal length (mm)
        b - baseline (mm)
        u0 - x offset in image coordinate
        v0 - y offset in image coordinate

    Attributes:
        f (float): Focal length in mm
        b (float): Base line in mm
        u0 (float): X offset in image coordinate
        v0 (float): Y offset in image coordinate
        FOV_H (float): Horizontal field of view in degrees
        FOV_V (float): Vertical field of view in degrees
        FOV_d (float): Diagonal field of view in degrees
        aperture (float): Aperture size
        resolution (tuple): Camera resolution (width, height)
        camera_left_id (int): Camera ID for the left camera
        camera_right_id (int): Camera ID for the right camera
        WIDTH (int): Image width for processing
        HEIGHT (int): Image height for processing
        FPS (float): Frames per second for video capture
        STERIO (bool): Whether stereo vision is enabled
    """

    # Calibration and camera parameters
    f = 2.6
    b = 60
    u0 = 2
    v0 = 1
    FOV_H = 73
    FOV_V = 50
    FOV_d = 83
    aperture = 2.4
    resolution = (3280 , 2464 )
    camera_left_id = 0
    camera_right_id = 1
    WIDTH = 640
    HEIGHT = 480
    FPS = 30.0
    STERIO = True

    def __init__(self, logger=None):
        """
        Initializes the Camera object, setting up the camera configurations and logger.
        """
        self.state = {
            "record": False,
            "recording": {
                "left": {"state": False, "fname": None},
                "right": {"state": False, "fname": None}
            },
            "active": False,
            "live": False
        }
        self.logger = logger
        self.exit = False
        self.set_config()

        try:
            self.cam_left = Picamera2(self.camera_left_id)
            video_config = self.cam_left.create_video_configuration(main=self.main, controls=self.controls)
            self.cam_left.configure(video_config)

            self.cam_right = Picamera2(self.camera_right_id)
            video_config = self.cam_right.create_video_configuration(main=self.main, controls=self.controls)
            self.cam_right.configure(video_config)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error initializing cameras: {e}")
            raise RuntimeError("Failed to initialize cameras")

    def set_config(self, fps=20, img_width=720, img_height=720, color_format="RGB888"):
        """
        Configures the camera settings including FPS, image dimensions, and color format.
        
        Args:
            fps (int): Frames per second.
            img_width (int): Width of the captured image.
            img_height (int): Height of the captured image.
            color_format (str): Color format for the captured image.
        """
        self.fps = fps
        self.img_width = img_width
        self.img_height = img_height
        self.size = (self.img_height, self.img_width)
        self.format = color_format
        self.fdl = (33333, 33333)

        if self.fps == 20:
            self.fdl = (40000, 40000)
        elif self.fps == 10:
            self.fdl = (100000, 100000)
        
        self.controls = {"FrameDurationLimits": self.fdl}
        self.main = {"size": self.size, "format": "RGB888"}

    def get_stream(self):
        """
        Retrieves a pair of stereo images (left and right) from the cameras if the system is live.
        
        Returns:
            tuple: (left_image, right_image) if live, otherwise None.
        """
        if self.state['live']:
            try:
                img_left = self.cam_left.read()
                img_right = self.cam_right.read()
                return (img_left, img_right)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error getting stream: {e}")
                return None
        return None

    def start_recording(self):
        """
        Starts the recording process, saving both left and right camera streams to video files.
        """
        self.state['record'] = True
        self.exit = False
        self.record()

    def end_recording(self):
        """
        Ends the recording process and waits for it to stop.
        """
        self.exit = True
        while self.state['record']:
            time.sleep(0.1)

    def set_state(self, recording_left=None, recording_right=None, active=None):
        """
        Sets the state of the camera system.
        
        Args:
            recording_left (dict): State for the left camera recording.
            recording_right (dict): State for the right camera recording.
            active (bool): Whether the camera system is active.
        """
        if recording_left:
            self.state['recording']['left'] = recording_left
        if recording_right:
            self.state['recording']['right'] = recording_right
        if active is not None:
            self.state['active'] = active

    def get_state(self):
        """
        Returns the current state of the camera system.
        
        Returns:
            dict: The current state.
        """
        return self.state

    def get_recording_state(self):
        """
        Returns whether the camera system is currently recording.
        
        Returns:
            bool: True if recording, False otherwise.
        """
        return self.state['record']

    def record(self):
        """
        Captures frames from both cameras and saves them as video files in the current directory.
        """
        try:
            file_name = str(int(time.time()))
            fname_l = f"left_{file_name}.avi"
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out_l = cv2.VideoWriter(fname_l, fourcc, self.FPS, self.size)

            fname_r = f"right_{file_name}.avi"
            out_r = cv2.VideoWriter(fname_r, fourcc, self.FPS, self.size)

            self.cam_left.start()
            self.cam_right.start()

            while True:
                if self.exit:
                    if self.logger:
                        self.logger.info('Ending recording...')
                    break

                frame_l = self.cam_left.capture_array()
                frame_r = self.cam_right.capture_array()

                out_r.write(frame_r)
                out_l.write(frame_l)

            self.cam_left.stop()
            self.cam_right.stop()

            out_l.release()
            out_r.release()

            self.cam_left.close()
            self.cam_right.close()

            self.set_state(
                {'state': True, 'fname': fname_l},
                {'state': True, 'fname': fname_r}
            )
            self.state['record'] = False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during recording: {e}")

    def get_recorded_file(self, sterio=True):
        """
        Retrieves the recorded video files for left and right cameras.

        Args:
            sterio (bool): Whether stereo video is enabled.

        Returns:
            tuple: Paths to the recorded video files.
        """
        if not sterio:
            return self.state['recording']['left']['fname']
        else:
            return self.state['recording']['left']['fname'], self.state['recording']['right']['fname']

    def get_recording(self, sterio=True):
        """
        Retrieves the recorded video data from both cameras.

        Args:
            sterio (bool): Whether stereo video is enabled.

        Returns:
            tuple: Recorded video data for left and right cameras.
        """
        rec_file_name = self.get_recorded_file()
        if not rec_file_name:
            return None, "No recording exists!"
        
        try:
            if not sterio:
                with open(rec_file_name, 'rb') as video:
                    rec_l = video.read()
                return ((rec_file_name, rec_l),), None

            with open(rec_file_name[0], 'rb') as video:
                rec_l = video.read()

            with open(rec_file_name[1], 'rb') as video:
                rec_r = video.read()

            return ((rec_file_name[0], rec_l), (rec_file_name[1], rec_r)), None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error retrieving recording: {e}")
            return None, f"Error retrieving recording: {e}"

    def capture_image(self):
        """
        Captures a single pair of stereo images from both cameras.

        Returns:
            tuple: A pair of images from the left and right cameras.
        """
        try:
            self.cam_left.start()
            self.cam_right.start()
            img_left = self.cam_left.capture_array()
            img_right = self.cam_right.capture_array()
            self.cam_left.stop()
            self.cam_right.stop()
            return img_left, img_right
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error capturing image: {e}")
            return None, None

    def cannyImage(self, image):
        """
        Applies Canny edge detection to an input image.

        Args:
            image (ndarray): The input image.

        Returns:
            ndarray: The edge-detected image.
        """
        try:
            grayScaleImage = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            bluredGSImage = cv2.GaussianBlur(grayScaleImage, (5, 5), 0)
            canny = cv2.Canny(bluredGSImage, 50, 150)
            return canny
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error applying Canny edge detection: {e}")
            return None

    def close(self):
        """
        Closes the camera connections.
        """
        try:
            self.cam_left.close()
            self.cam_right.close()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error closing cameras: {e}")
