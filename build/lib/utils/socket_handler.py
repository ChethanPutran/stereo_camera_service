import socket
import threading
import logging
import pickle
import struct
import time
from abc import ABC, abstractmethod
from typing import Callable, Any
from config.settings import HEADER_SIZE


class Streamer(ABC):
    """
    Abstract base class representing a stream source.
    A subclass should implement get_stream() that returns the data to be streamed.
    """
    @abstractmethod
    def get_stream(self) -> Any:
        """
        Returns the next frame or data from the stream source.
        """
        pass


class SocketHandler:
    """
    A class to handle socket-based communication for client and server,
    including support for live streaming using a Streamer class.
    """
    TYPE_CLIENT = 'client'
    TYPE_SERVER = 'server'
    print_lock = threading.Lock()
    header_size = HEADER_SIZE # Used for receiving fixed-length headers

    def __init__(self, host: str, port: int, type=TYPE_CLIENT):
        """
        Initializes the socket handler with host, port, logger, and type (client/server).
        """
        self.logger = logging.getLogger()
        self.type = type
        self.host = host
        self.port = port
        self.reciever = None
        self.reciever_addr = None
        self.is_inilialized = False

    def init_reciever(self):
        self.is_inilialized = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """
        Initializes the connection as either a server or client.
        """
        if self.type == self.TYPE_SERVER:
            self.bind_socket()
            self.accept_connection()
        else:
            try:
                self.socket.connect((self.host, self.port))
                self.reciever = self.socket
            except ConnectionRefusedError as e:
                self.logger.error("Server not found!")
                exit(0)

    def send(self, message: Any,show=True) -> None:
        """
        Serializes and sends a Python object over the socket connection.

        Args:
            message: Any serializable Python object.
        """
        try:
            if show:
                self.logger.debug(f"Sending message: {message}")
            body = pickle.dumps(message)
            header = struct.pack("L", len(body))  # Corrected to use `body` instead of `req`
            req = header + body
            self.reciever.sendall(req)
            self.logger.debug("Request sent.")
        except Exception as e:
            self.handle_connection_close()

    def send_live_stream(self, streamer: Streamer, separe_thread=False) -> None:
        """
        Continuously sends live data from a streamer

        Args:
            streamer: An object of a class that implements Streamer.
            separe_thread: Whether to run streaming in a separate thread.
        """

        if not self.is_inilialized:
            self.init_reciever()
            
        def loop():
            count = 0
            while True:
                count+=1
                with self.print_lock:
                    print("Frame  :"+str(count))
                status,stream = streamer.get_stream()
                if not status:
                    self.send('<END>')
                    break
                self.send(stream,show=False)
                time.sleep(0.03)

              # Send termination message
            with self.print_lock:
                print("Live ended.")

        if separe_thread:
            th = threading.Thread(target=loop)
            th.start()
            # th.join()
        else:
            loop()

    def recive_live_stream(self, stream_callback: Callable[[bool, Any], Any], separe_thread=False) -> None:
        """
        Receives a continuous stream and processes each packet via a callback.

        Args:
            stream_callback: A function that receives (bool, data).
            separe_thread: Whether to run receiving in a separate thread.
        """ 

        if not self.is_inilialized:
            self.init_reciever()

        def loop():
            self.logger.info('Receiving live stream...')
            data = b''

            # Receive the fixed-size header
            msg = self.reciever.recv(self.header_size)
            msg_size = struct.unpack("L", msg)[0] 
            while True:
                # Receive the message based on the size from the header
                while len(data) < msg_size:
                    data += self.reciever.recv(4096)

                frame_data = data[:msg_size]
                data = data[msg_size:]

                frames = pickle.loads(frame_data)
                if frames == "<END>":
                    self.logger.info('Ending live capture...')
                    stream_callback(False, None)
                    break

                stream_callback(True, frames)

                if len(data) < self.header_size:
                    stream_callback(False, None)
                    break
                msg = data[:self.header_size]
                msg_size = struct.unpack("L", msg)[0] 
                data = data[self.header_size:]

        if separe_thread:
            th = threading.Thread(target=loop)
            th.start()
            # th.join()
        else:
            loop()

    def handle_connection_close(self):
        if self.type == self.TYPE_CLIENT:
            self.logger.error("Server unavailable!")
            exit(0)
        else:
            self.logger.error("Client disconnected!")
            self.accept_connection()

    def recieve(self, is_file=False, large_file=False) -> Any:
        """
        Receives and deserializes a complete message from the socket.

        Args:
            is_file: Whether the data is a file.
            large_file: Whether it's a large file requiring bigger buffer.

        Returns:
            Deserialized Python object.
        """
        try:
            self.logger.debug("Receiving...")
            res = b''
            msg_len = 0

            # Unpack the binary header to get message length

            msg = self.reciever.recv(self.header_size)
            msg_len = struct.unpack("L", msg)[0]   # returns a tuple, get the first item

            buff_size = 4096 if large_file else 1024 if is_file else 16

            while True:
                msg = self.reciever.recv(buff_size)
            
                if not msg:
                    break
                
                res += msg

                if len(res)== msg_len:
                    break

            res = pickle.loads(res)
            self.logger.debug("Received.")
            return res
        except Exception as e:
            self.handle_connection_close()

    def close(self):
        """
        Closes the socket connection.
        """
        if self.socket:
            self.socket.close()
        self.logger.info("Socket closed. Bye!")

    def accept_connection(self):
        """
        For server mode: accepts an incoming connection.
        """
        self.logger.info("Waiting for connection...")
        self.reciever, self.reciever_addr = self.socket.accept()
        self.logger.info(f'Connection established from {self.reciever_addr[0]}')

    def bind_socket(self):
        """
        For server mode: binds and listens on the specified host and port.
        Retries on failure.
        """
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.logger.info(f"Server listening at {self.host}:{self.port}")
        except socket.error as msg:
            self.logger.error(f"Socket Binding Error: {msg}")
            self.logger.info("Retrying...")
            self.bind_socket()
