import socket
import threading
import logging
import pickle
import struct
from abc import ABC
from abc import abstractmethod
from typing import Callable,Any

class Streamer(ABC):
    @abstractmethod
    def get_stream(self)->Any:
        pass

class SocketHandler:
    TYPE_CLIENT = 'client'
    TYPE_SERVER = 'server'
    def __init__(self, host:str, port:int,logger:logging.Logger,type=TYPE_CLIENT):
        self.logger = logger
        self.type = type
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reciever = None
        self.reciever_addr = None
        self.end_live = None
        self.init_reciever()

    def init_reciever(self):
        if self.type == self.TYPE_SERVER:
            self.bind_socket()
            self.accept_connection()
        else:
            self.socket.connect((self.host, self.port))
            self.reciever = self.socket

    def send(self,message:Any)->None:
        self.logger.debug(f"Sending message : {message}")
        body = pickle.dumps(message)
        header = struct.pack("L", len(req))
        req = header + body
        self.reciever.sendall(req)
        self.logger.debug("Request sent.")

    def send_live_stream(self,streamer:Streamer,separe_thread=False)->None:
        def loop():
            # End the live stream if status is False
            while self.end_live.is_set():
                # Send each packet of the stream
                stream = streamer.get_stream()
                self.send(stream)
                # time.sleep(0.1)
            
            # Send the END token to indicate the end of the stream
            self.send('<END>')

        if separe_thread:
            self.end_live = threading.Event()
            th = threading.Thread(target=loop)
            th.start()
            th.join()
        else:
            loop() 
    
    def recive_live_stream(self,stream_callback:Callable[[bool, Any], Any],separe_thread=False)->None:
        def loop():
            self.logger.info('Recieving live stream...')
            data = b''
            payload_size = struct.calcsize("L") 

            while not self.end_live.is_set():
                # Recieve the header
                while len(data) < payload_size:
                    data += self.reciever.recv(4096)

                # Extract the header & get the message size
                packed_msg_size = data[:payload_size]
                msg_size = struct.unpack("L", packed_msg_size)[0]

                # Remove the header from the data 
                data = data[payload_size:]

                # Recieve the packets & construct the message
                while len(data) < msg_size:
                    data += self.reciever.recv(4096)

                # Obtain the current frame data from the buffer
                frame_data = data[:msg_size]

                # Keep the remaining data
                data = data[msg_size:]

                # Check if the data is the end of the stream
                if frame_data == b"<END>":
                    self.logger.info('Ending live capture...')
                    self.live_ended = True
                    stream_callback(False,None)
                    continue

                # Obtain the image from the buffer 
                frame=pickle.loads(frame_data)
                stream_callback(True,frame)
        
        if separe_thread:
            self.end_live = threading.Event()
            th = threading.Thread(target=loop)
            th.start()
            th.join()
        else:
            loop()
        
    def end_live_stream(self):
        self.end_live.set()

    def recieve(self,is_file=False,large_file=False)->Any:
        self.logger.debug("Recieving...")
        new_msg = True
        res = b''
        msg_len = 0

        buff_size = 16

        if is_file:
            if large_file:
                buff_size = 4096
            else:
                buff_size = 1024

        while True:
            self.logger.debug('.')
            msg = self.reciever.recv(buff_size)
            
            if not len(msg):
                break

            # Get the message size whenever a new message is recieved
            if new_msg:
                msg_len = int(msg[:self.header_size])
                new_msg = False

            # Construct the message
            res += msg

            ## Check if the message is complete
            if(len(res)-self.header_size == msg_len):
                new_msg = True
                res = res[self.header_size:]
                break
        
        # Parse the message
        res = pickle.loads(res)

        self.logger.debug("Recieved.")
        self.logger.debug(res)
        return res

    def close(self):
        if self.socket:
            self.socket.close() 
        self.logger.info("Exiting... Bye!")
    
    def accept_connection(self):
        #Accepting the connection requrest
        self.logger.info("Waiting for connection...")
        self.reciever,  self.reciever_addr = self.socket.accept()
        self.logger.info(f'Connection has been established from {self.reciever_addr[0]}')

    def bind_socket(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.logger.info(f"Server listening at {self.host}:{self.port}")
        except socket.error as msg:
            self.logger.error(f"Scoket Binding Error: {msg}")
            self.logger.info("Retrying...")
            self.bind_socket()