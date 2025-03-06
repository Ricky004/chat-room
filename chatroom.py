import socket
import threading
from io import BytesIO
from collections import deque

from message import Message


MAX_PARTICIPANTS = 10

class Participant:
    '''A class to represent a participant in a chatroom'''

    def __init__(self):
        self.message = None

    def write(self, message: str):
        self.message = Message(message)

    def deliver(self):
        return self.message
    

class Room:
    '''A class to represent a chatroom'''
    
    def __init__(self):
        self.message_queue = deque()
        self.participants = {}

    def join(self, participant: Participant):
        self.participants.append(participant)
    
    def leave(self, participant: Participant):
        self.participants.remove(participant)

    def deliver(self, participant: Participant, message: Message):
        self.message_queue.append(message)
        while self.message_queue:
            msg = self.message_queue.popleft()

            for p in self.participants:
                if p != participant:
                    p.write(msg)
                    p.deliver()
    


class Session(Participant):
    '''A class to represent a chatroom session'''

    def __init__(self, socket: socket.socket, room: Room):
        super().__init__()
        self.socket = socket
        self.room = room
        self.buffer = BytesIO()
        self.message_queue = deque()

    def start(self):
        self.room.join(self)
        self.async_read()

    def write(self, message: Message):
        self.message_queue.append(message)
        while len(self.message_queue) != 0:
            message = self.message_queue.popleft()
            header_decode = message.decode_header()
            if header_decode:
                body = message.data
                self.async_write(body, message.get_new_body_length())
            else:
                print("Error: Message too long")
    
    def deliver(self, message: Message):
        self.room.deliver(self, message)
        

    def async_write(self, body: bytearray, body_length: int):
        pass

    def async_read(self):
        pass
    

class ChatServer:
    '''A server that accepts incoming connections and creates Sessions.'''

    def __init__(self, host: str, port: int, room: Room):
        self.host = host
        self.port = port
        self.room = room
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server listening on {host}:{port}")

    def accept_connection(self):
        try:
            client_socket, addr = self.server_socket.accept()
            print("Accepted connection from:", addr)
            session = Session(client_socket, self.room)
            return session
        except Exception as e:
            print("Error accepting connection:", e)
            return None

