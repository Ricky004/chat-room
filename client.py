import socket
import struct

from chatroom import Room, Session
from message import Message, MAX_BYTES, HEADER

def main():
    host = 'localhost'  
    port = 12345

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")
    except Exception as e:
        print("Error connecting to server:", e)
        return

    room = Room()
    session = Session(client_socket, room)

    while True:
        user_input = input("Enter message (or 'exit' to quit): ").strip()
        if user_input.lower() == "exit":
            break
        if not user_input:
            print("Empty message. Try again.")
            continue

        msg_body = user_input[:MAX_BYTES]
        header = struct.pack("!I", len(msg_body))
        full_msg = header + msg_body.encode("utf-8")
            
        try:
            client_socket.sendall(full_msg)  # Send both header and message
            print(f"Sent: {msg_body}")
        except Exception as e:
            print("Error sending message:", e)
            break

    client_socket.close()
    print("Connection closed. Goodbye!")

if __name__ == "__main__":
    main()
