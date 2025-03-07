import socket
import threading
import struct

from message import Message, HEADER, MAX_BYTES

class ChatClient:
    def __init__(self, host: str, port: int, username: str):
        self.host = host
        self.port = port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
    
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"Connected to server at {self.host}:{self.port}")
            
            # Start thread for receiving messages
            receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def send_message(self, text: str):
        if not self.running:
            print("Not connected to server")
            return False
        
        try:
            message = Message(text)
            self.socket.sendall(message.get_data())
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            self.running = False
            return False
    
    def _receive_messages(self):
        while self.running:
            try:
                # Read header
                header_bytes = self._recv_exact(HEADER)
                if not header_bytes:
                    print("Disconnected from server")
                    self.running = False
                    break
                
                # Get message length
                msg_length = struct.unpack("!I", header_bytes)[0]
                if msg_length <= 0 or msg_length > MAX_BYTES:
                    print(f"Invalid message length: {msg_length}")
                    self.running = False
                    break
                
                # Read message body
                message_bytes = self._recv_exact(msg_length)
                if not message_bytes:
                    print("Disconnected while reading message")
                    self.running = False
                    break
                
                # Display the message
                message = message_bytes.decode("utf-8")
                print(message)
                
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.running = False
                break
    
    def _recv_exact(self, num_bytes: int) -> bytes:
        data = b""
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def close(self):
        """Close the connection to the server"""
        self.running = False
        self.socket.close()
        print("Disconnected from server")

if __name__ == "__main__":
    host = input("Enter server IP: ")
    port = int(input("Enter server port: "))
    username = input("Enter your username: ")
    
    client = ChatClient(host, port, username)
    if client.connect():
        while True:
            message = input()
            if message.lower() == "exit":
                client.close()
                break
            client.send_message(message)
