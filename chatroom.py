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

    def deliver(self, participant: Participant, message: str):
        return participant.deliver(message)


class Session(Participant):
    '''A class to represent a chatroom session'''

    def __init__(self, socket: socket.socket, room: Room):
        super().__init__()
        self.socket = socket
        self.room = room
        self.buffer = BytesIO()
        self.message_queue = deque()

    def start(self):
        pass

    def write(self):
        pass
    
    def deliver(self):
        pass

    def async_write(self):
        pass

    def async_read(self):
        pass



