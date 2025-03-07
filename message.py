import struct

HEADER = 4
MAX_BYTES = 512

class Message:
    '''A class to represent a message in a chatroom'''
    
    def __init__(self, message: str | None): 
        if message is None:
            self.body = b""
        else:
            self.body = message[:MAX_BYTES].encode("utf-8") if isinstance(message, str) else message[:MAX_BYTES]
        
        self.body_length = len(self.body)
        self.header = struct.pack("!I", self.body_length)
        self.data = self.header + self.body  

    def decode_header(self) -> bool:
        if len(self.header) < HEADER:
           print("Invalid header length")
           return False
       
        self.body_length = struct.unpack("!I", self.data[:HEADER])[0]
        if self.body_length > MAX_BYTES:
            print("Message too long")
            return False
        return True

    def get_data(self) -> bytes:
        return self.data  

    @staticmethod
    def from_bytes(raw_data: bytes):
        if len(raw_data) < HEADER:
            raise ValueError("Data too short")

        header = raw_data[:HEADER]
        body_length = struct.unpack("!I", header)[0]

        if body_length > MAX_BYTES:
            raise ValueError("Data too long")

        body = raw_data[HEADER:HEADER + body_length]
        return Message(body)      