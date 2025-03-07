import socket
import threading
import struct
from collections import deque

from message import Message, HEADER, MAX_BYTES


MAX_PARTICIPANTS = 10

class Participant:
    '''A class to represent a participant in a chatroom'''

    def __init__(self):
        self.message = deque()

    def write(self, message: Message):
        self.message.append(message)

    def deliver(self):
        return self.message
    

class Room:
    '''A class to represent a chatroom'''
    
    def __init__(self):
        self.participants = []

    def join(self, participant: Participant):
        self.participants.append(participant)
    
    def leave(self, participant: Participant):
        if participant in self.participants:
           self.participants.remove(participant)

    def broadcast(self, message: Message, sender: Participant):
        for p in self.participants:
            if p != sender:
                p.write(message)
                if hasattr(p, 'async_write'):
                    p.async_write(message.get_data())


class Session(Participant):
    '''A class to represent a chatroom session'''

    def __init__(self, socket: socket.socket, room: Room):
        super().__init__()
        self.socket = socket
        self.room = room
        self.running = True
        self.message_queue = deque()

    def start(self):
        self.room.join(self)
        print(f"Session started for {self.socket.getpeername()}")  
        self._start_async_read()

    def _start_async_read(self):
        thread = threading.Thread(target=self._async_read, daemon=True)
        thread.start()

    
    def deliver(self, message: Message):
        self.room.deliver(self, message)

    def write(self, message: Message):
        self.message_queue.append(message)
        while self.message_queue:
            msg = self.message_queue.popleft()  
            self.async_write(msg.get_data())
            

    def async_write(self, data: bytes):

        def write():
            try:
                self.socket.sendall(data)
                print(f"Async write: sent {len(data)} bytes")
            except Exception as e:
                print("Error in async_write:", e)
        
        threading.Thread(target=write, daemon=True).start()


    def _async_read(self):
            while self.running:
                try:
                    # Step 1: Read exactly HEADER bytes for the header (binary)
                    header_bytes = self._recv_exact(HEADER)
                    if not header_bytes:
                        print("Connection closed (header)")
                        break   

                    # Step 2: Unpack the header to get message length
                    msg_length = struct.unpack("!I", header_bytes)[0]
                    if msg_length <= 0 or msg_length > MAX_BYTES:
                        print(f"Invalid message length: {msg_length}")
                        break

                    # Step 3: Read the full message body based on msg_length
                    message_bytes = self._recv_exact(msg_length)
                    if not message_bytes:
                        print("Connection closed (body)")
                        break

                    # Step 4: Create a Message object
                    full_message = header_bytes + message_bytes
                    msg = Message.from_bytes(full_message)

                    # Step 5: Properly handle the received message
                    self.handle_received_message(msg)

                except Exception as e:
                    print("Error in async_read:", e)
                    break

            self.close()

    def _recv_exact(self, num_bytes: int) -> bytes:
        data = b""
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def handle_received_message(self, message: Message):
        try:
            # Using Message.body to store the raw message bytes
            decoded = message.body.decode("utf-8") if isinstance(message.body, bytes) else message.body
            print(f"Received message from client: {decoded}")
        except Exception as e:
            print("Error decoding message:", e)
            return
        # Broadcast the message to other participants in the room
        self.room.broadcast(message, self)

    def close(self):
        self.running = False
        self.room.leave(self)
        try:
            peer = self.socket.getpeername()
            self.socket.close()
            print(f"Session closed for {peer}")
        except:
            self.socket.close()
            print("Session closed")


class ChatServer:
    '''A server that accepts incoming connections and creates Sessions.'''

    def __init__(self, host: str, port: int, room: Room):
        self.host = host
        self.port = port
        self.room = room
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server listening on {host}:{port}")

    def accept_connection(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"New connection from {addr}")

            session = Session(client_socket, self.room)
            session.start()


if __name__ == "__main__":
    room = Room()
    server = ChatServer('localhost', 12345, room)
    print("Server started")
    server.accept_connection()
        