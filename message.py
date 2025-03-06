import socket
import threading


HEADER = 4
MAX_BYTES = 512

class Message:

    def __init__(self, message: str = None): 
        self.data = bytearray(HEADER + MAX_BYTES)
        if message is None:
            self.body_length = 0
        else:
            self.body_length = self.get_new_body_length(len(message))
            self.encode_header()
            self.data[HEADER:HEADER+MAX_BYTES] = message[:self.body_length]

    def get_new_body_length(self, new_length: int) -> int:
        if new_length > MAX_BYTES:
            return MAX_BYTES
        else:
            return new_length
        
    def encode_header(self):
        new_header = bytearray(HEADER + 1)
        print(f"{int(self.body_length):4d}")
        self.data[:HEADER] = new_header[:HEADER]
        return self.data

    def decode_header(self) -> bool:
        new_header = bytearray(HEADER + 1)
        new_header[:HEADER] = self.data[:HEADER]
        new_header[HEADER] = "\0"
        header_value = int(new_header)
        if header_value > MAX_BYTES:
            self.body_length = 0
            return False
        else:
            self.body_length = header_value
            return True

        