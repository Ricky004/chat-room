import socket
import threading
import struct
from collections import deque

from message import Message, HEADER, MAX_BYTES
from client import ChatClient


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
        self.broadcast(Message("A new participant has joined the room"), participant)
    
    def leave(self, participant: Participant):
        if participant in self.participants:
           self.participants.remove(participant)
           self.broadcast(Message("A user has left the room"), None)

    def broadcast(self, message: Message, sender: Participant):
        for p in self.participants:
            if p != sender:
                p.write(message)
                if hasattr(p, 'process_outgoing_messages'):
                    p.process_outgoing_messages()


class Session(Participant):
    '''A class to represent a chatroom session'''

    def __init__(self, socket: socket.socket, room: Room, username=None):
        super().__init__()
        self.socket = socket
        self.room = room
        self.username = username or f"user:{id(self) % 1000}"
        self.running = True
        self.message_processing_lock = threading.Lock()
        self.message_queue = deque()

    def start(self):
        self.room.join(self)
        print(f"Session started for {self.username} at {self.socket.getpeername()}")  
        self._start_message_threads()

        # welcome messages
        welcome_msg = Message(f"Welcome to the chat, {self.username}!")
        self.write(welcome_msg)
        self.process_outgoing_messages()


    def _start_message_threads(self):
        read_thread = threading.Thread(target=self._message_reader_loop, daemon=True)
        write_thread = threading.Thread(target=self._message_writer_loop, daemon=True)

        read_thread.start()
        write_thread.start()


    def _message_writer_loop(self):
        while self.running:
            try:
                if self.message_queue:
                    self.process_outgoing_messages()

                threading.Event().wait(0.1)
            except Exception as e:
                print(f"Error writing message to {self.username}: {e}")
                break
    

    def _message_reader_loop(self):
            while self.running:
                try:
                    # Step 1: Read exactly HEADER bytes for the header (binary)
                    header_bytes = self._recv_exact(HEADER)
                    if not header_bytes:
                        print(f"Connection closed for {self.username} (header)")
                        break   

                    # Step 2: Unpack the header to get message length
                    msg_length = struct.unpack("!I", header_bytes)[0]
                    if msg_length <= 0 or msg_length > MAX_BYTES:
                        print(f"Invalid message length: {msg_length}")
                        break

                    # Step 3: Read the full message body based on msg_length
                    message_bytes = self._recv_exact(msg_length)
                    if not message_bytes:
                        print(f"Connection closed for {self.username} (body)")
                        break

                    # Step 4: Create a Message object
                    full_message = header_bytes + message_bytes
                    msg = Message.from_bytes(full_message)

                    # Step 5: Properly handle the received message
                    self.handle_incoming_message(len(msg))

                except Exception as e:
                    print(f"Error reading message from {self.username}: {e}")
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
    

    def handle_incoming_message(self, raw_message: bytes):
        try:
            message = Message.from_bytes(raw_message)
            
            decoded_body = message.body.decode("utf-8") if isinstance(message.body, bytes) else message.body
            
            print(f"Message from {self.username}: {decoded_body}")
            
            formatted_message = f"{self.username}: {decoded_body}"
            broadcast_message = Message(formatted_message)
            
            self.room.broadcast(broadcast_message, self)
            
        except Exception as e:
            print(f"Error handling incoming message: {e}")


    def process_outgoing_messages(self):
            """Process and send all queued messages"""
            with self.message_processing_lock:
                while self.message_queue:
                    message = self.message_queue.popleft()
                    try:
                        self.socket.sendall(message.get_data())
                    except Exception as e:
                        print(f"Error sending message to {self.username}: {e}")
                        self.running = False
                        break


    def close(self):
        if not self.running:
            return
        
        self.running = False
        self.room.leave(self)

        try:
            peer = self.socket.getpeername()
            self.socket.close()
            print(f"Session closed for {self.username} at {peer}")
        except:
            self.socket.close()
            print(f"Session closed for {self.username}")


class ChatServer:
    '''A server that accepts incoming connections and creates Sessions.'''

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.room = Room()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")
        
        try:
            self._accept_connections()
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.server_socket.close()

    def _accept_connections(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"New connection from {addr}")

            session = Session(client_socket, self.room)
            session.start()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "client":
        # Run as client
        username = sys.argv[2] if len(sys.argv) > 2 else f"User-{id(object()) % 1000}"
        client = ChatClient("localhost", 12345, username)
        
        if client.connect():
            print(f"Connected as {username}. Type your messages (or 'quit' to exit):")
            try:
                while True:
                    message = input("> ")
                    if message.lower() == "quit":
                        break
                    client.send_message(message)
            except KeyboardInterrupt:
                print("\nExiting...")
            finally:
                client.close()
    else:
        # Run as server
        server = ChatServer("localhost", 12345)
        print("Chat server starting...")
        server.start()        