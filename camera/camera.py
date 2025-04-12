import cv2   
import time
import numpy as np
from utils.socket_handler import Streamer
from abc import override

try:
    from picamera2 import Picamera2
except Exception as e:
    class Picamera2:
        pass

    
class CameraInterface:
    pass
class Camera(Streamer):

    """ 
    ***** Calibration params (f, b, u0, v0) *****

    f - focal length
    b - base line
    u0 - x offset in image coordinate
    v0 - y offset in image coordinate

    """
    f = 2.6  # in mm
    b = 60   # in mm
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

    def __init__(self,logger=None):
        self.state = {
           "record":False,
           "recording":{
           "left":{
            "state":False,
            "fname":None
           },
           "right":{
            "state":False,
            "fname":None
           },
           },
           "active":False,
           "live":False
        }
        self.logger = logger
        self.exit =False
        self.set_config()
        self.cam_left = Picamera2(self.camera_left_id)
        video_config = self.cam_left.create_video_configuration(main=self.main,controls=self.controls)
        self.cam_left.configure(video_config)
        self.cam_right = Picamera2(self.camera_right_id)
        # time.sleep(2)
        video_config =  self.cam_right.create_video_configuration(main=self.main,controls=self.controls)
        self.cam_right.configure(video_config)

    def set_config(self,fps=20,img_width=720,img_height=720,color_format="RGB888"):
        self.fps = fps
        self.img_width = img_width
        self.img_height = img_height
        self.size = (self.img_height,self.img_width)
        self.format = color_format
        self.fdl = (33333,33333)

        if self.fps == 20:
            self.fdl = (40000,40000)
        elif self.fps == 10:
            self.fdl = (100000,100000)
        
        self.controls = {"FrameDurationLimits":self.fdl}
        self.main = {"size": self.size,"format":"RGB888"}

    @override
    def get_stream(self):
        if self.state['live']:
            img_left = self.camera_left.read()
            img_right = self.camera_right.read()
            return (img_left,img_right)
        return None
    
    def start_recording(self):
        self.state['record'] = True
        self.exit = False
        self.record()

    def end_recording(self):
        self.exit = True

        # Wait untill recording get stopped
        while self.state['record']:
            time.sleep(0.1)

    def set_state(self,recording_left=None,recording_right=None,active=None):
        if recording_left:
            self.state['recording']['left'] = recording_left
        if recording_right:
            self.state['recording']['right'] = recording_right
        if not(active == None):
            self.state['active'] = active

    def get_state(self):
        return self.state
    
    def get_recording_state(self):
        return self.state['record']
    
    def record(self):
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
                    self.logger.info('Ending recording...')
                    break

                frame_l = self.cam_left.capture_array()
                frame_r = self.cam_right.capture_array()

                out_r.write(frame_r)
                out_l.write(frame_l)
            
                # img = self.camera.getImageArray()
                # img = np.asarray(img, dtype=np.uint8)
                # img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                # img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                # img = cv2.flip(img, 1)

            self.cam_left.stop()
            self.cam_right.stop()
          
            out_l.release()
            out_r.release()

            self.cam_left.close()
            self.cam_right.close()
                

            self.set_state({'state':True,
                             'fname':fname_l},
                                    {
                                        'state':True,
                                        'fname':fname_r
                                    })
            self.state['record'] = False

        except Exception as e:
            self.logger.error(e)

    def get_recorded_file(self,sterio=STERIO):
        if not sterio:
            return self.state['recording']['left']['fname']
        else:
            return self.state['recording']['left']['fname'],self.state['recording']['right']['fname']

    def get_recording(self,sterio=STERIO):
        rec_file_name = self.get_recorded_file()
        self.logger.debug(f"Rec file : {rec_file_name}")
        if not rec_file_name:
            return None,"No recording exits!"
    
        if not sterio:
            with open(rec_file_name, 'rb') as video:
                rec_l = video.read()
            return ((rec_file_name,rec_l),), None
        
        with open(rec_file_name[0], 'rb') as video:
            rec_l = video.read()
        
        with open(rec_file_name[1], 'rb') as video:
            rec_r = video.read()

        return ((rec_file_name[0],rec_l),(rec_file_name[1],rec_r),),None
    
    def capture_image(self):
        self.cam_left.start()
        self.cam_right.start()      
        img_left = self.cam_left.capture_array()
        img_right = self.cam_right.capture_array()
        self.cam_left.stop()
        self.cam_right.stop()
        return (img_left,img_right)

    def get_sterio_frame(self):
        img_left = self.cam_left.capture_array()
        img_right = self.cam_right.capture_array()
        return (img_left,img_right)

    def cannyImage(self, image):
        # 1.Conveting coloured image to grayscale image
        grayScaleImage = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # 2.Reducing noise and smoothening image
        bluredGSImage = cv2.GaussianBlur(grayScaleImage, (5, 5), 0)

        # Determing the edges based on gradient(taking derivative(f(x,y)) x->along width of the message y-> along height)
        # (image,low_threshold,hight_threshold)
        canny = cv2.Canny(bluredGSImage, 50, 150)

        return canny
         
    def enable(self,sampling_period):
      pass

    def segment(self):
      img = self.get_image_from_camera()

      # Segment the image by color in HSV color space
      img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
      mask = cv2.inRange(img, np.array([50, 150, 0]), np.array([200, 230, 255]))

      # Find the largest segmented contour (red ball) and it's center
      contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
      largest_contour = max(contours, key=cv2.contourArea)
      largest_contour_center = cv2.moments(largest_contour)
      center_x = int(largest_contour_center['m10'] / largest_contour_center['m00'])

      # Find error (ball distance from image center)
      error = self.camera.getWidth() / 2 - center_x

    def is_live_streaming(self)->bool:
        return self.state['live']
    
    def stop_live_streaming(self)->None:
        self.state['live'] = False
    
    def close(self):
        self.cam_left.close()
        self.cam_right.close()
       

