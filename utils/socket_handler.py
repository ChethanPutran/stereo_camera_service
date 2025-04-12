import socket
import threading
import logging
import pickle
import struct
from abc import ABC, abstractmethod
from typing import Callable, Any

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

    def __init__(self, host: str, port: int, logger: logging.Logger, type=TYPE_CLIENT):
        """
        Initializes the socket handler with host, port, logger, and type (client/server).
        """
        self.logger = logger
        self.type = type
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reciever = None
        self.reciever_addr = None
        self.end_live = None
        self.header_size = struct.calcsize("L")  # Used for receiving fixed-length headers
        self.init_reciever()

    def init_reciever(self):
        """
        Initializes the connection as either a server or client.
        """
        if self.type == self.TYPE_SERVER:
            self.bind_socket()
            self.accept_connection()
        else:
            self.socket.connect((self.host, self.port))
            self.reciever = self.socket

    def send(self, message: Any) -> None:
        """
        Serializes and sends a Python object over the socket connection.

        Args:
            message: Any serializable Python object.
        """
        self.logger.debug(f"Sending message: {message}")
        body = pickle.dumps(message)
        header = struct.pack("L", len(body))  # Corrected to use `body` instead of `req`
        req = header + body
        self.reciever.sendall(req)
        self.logger.debug("Request sent.")

    def send_live_stream(self, streamer: Streamer, separe_thread=False) -> None:
        """
        Continuously sends live data from a streamer until end_live is cleared.

        Args:
            streamer: An object of a class that implements Streamer.
            separe_thread: Whether to run streaming in a separate thread.
        """
        def loop():
            while self.end_live.is_set():
                stream = streamer.get_stream()
                self.send(stream)
                # Add delay if needed using time.sleep()

            self.send('<END>')  # Send termination message

        self.end_live = threading.Event()
        self.end_live.set()

        if separe_thread:
            th = threading.Thread(target=loop)
            th.start()
            th.join()
        else:
            loop()

    def recive_live_stream(self, stream_callback: Callable[[bool, Any], Any], separe_thread=False) -> None:
        """
        Receives a continuous stream and processes each packet via a callback.

        Args:
            stream_callback: A function that receives (bool, data).
            separe_thread: Whether to run receiving in a separate thread.
        """
        def loop():
            self.logger.info('Receiving live stream...')
            data = b''

            while not self.end_live.is_set():
                # Receive the fixed-size header
                while len(data) < self.header_size:
                    data += self.reciever.recv(4096)

                packed_msg_size = data[:self.header_size]
                msg_size = struct.unpack("L", packed_msg_size)[0]
                data = data[self.header_size:]

                # Receive the message based on the size from the header
                while len(data) < msg_size:
                    data += self.reciever.recv(4096)

                frame_data = data[:msg_size]
                data = data[msg_size:]

                if frame_data == b"<END>":
                    self.logger.info('Ending live capture...')
                    stream_callback(False, None)
                    return

                frame = pickle.loads(frame_data)
                stream_callback(True, frame)

        self.end_live = threading.Event()
        self.end_live.clear()

        if separe_thread:
            th = threading.Thread(target=loop)
            th.start()
            th.join()
        else:
            loop()

    def end_live_stream(self):
        """
        Terminates live streaming by setting the event flag.
        """
        if self.end_live:
            self.end_live.clear()

    def recieve(self, is_file=False, large_file=False) -> Any:
        """
        Receives and deserializes a complete message from the socket.

        Args:
            is_file: Whether the data is a file.
            large_file: Whether it's a large file requiring bigger buffer.

        Returns:
            Deserialized Python object.
        """
        self.logger.debug("Receiving...")
        new_msg = True
        res = b''
        msg_len = 0

        buff_size = 4096 if large_file else 1024 if is_file else 16

        while True:
            msg = self.reciever.recv(buff_size)
            if not msg:
                break

            if new_msg:
                msg_len = int(msg[:self.header_size])
                new_msg = False

            res += msg

            if len(res) - self.header_size == msg_len:
                res = res[self.header_size:]
                break

        res = pickle.loads(res)
        self.logger.debug("Received.")
        return res

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
