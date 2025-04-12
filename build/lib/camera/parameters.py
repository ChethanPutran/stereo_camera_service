
f = 2.6  # in mm
b = 60   # in mm
u0 = 2
v0 = 1
FOV_H = 73
FOV_V = 50
FOV_d = 83
aperture = 2.4
resolution = (3280 , 2464 )
camera_left = 0
camera_right = 1
WIDTH = 640
HEIGHT = 480
FPS = 30.0


# Assume z axis of robot and camera co-insides
# At a distance of 1m for the robot base (1m along base z axis) (100cm)
T_0_cam = [
    [1,0,0,0],
    [0,-1,0,0],
    [0,0,-1,100],
    [0,0,0,1],
           ]
