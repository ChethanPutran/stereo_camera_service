
   # if DEBUG:
    #     logging.basicConfig(filename="app_s.log", level=logging.DEBUG, 
    #                     format="%(asctime)s - %(levelname)s - %(message)s")
    # else:
    #     logging.basicConfig(filename="app_s.log", level=logging.INFO, 
    #                     format="%(asctime)s - %(levelname)s - %(message)s")  

  # class StreamGenerator:
    #     def __init__(self):
    #         self.cap = cv2.VideoCapture(r"test.mp4")
    #         if not self.cap.isOpened():
    #             print("Error: Could not open video.")
    #             exit()

    #     def get_stream(self):
    #         return self.cap.read()
    
    # # Testing
    # sg = StreamGenerator()
    # server = CameraServer("localhost")
    # server.send("Hello")
    # print(server.recieve())

    # img = cv2.imread("test.jpg")
    # # server.send_live_stream(sg.get_stream)
    # server.send(message="test",data=img)
    # print(server.recieve())
    # server.close()