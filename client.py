import curses
import socket
import threading
import struct

from message import Message, HEADER, MAX_BYTES


def recv_exact(sock, num_bytes):
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def receive_messages(chat_win, sock):
    while True:
        try:
            header_bytes = recv_exact(sock, HEADER)
            if not header_bytes:
                break

            msg_length = struct.unpack("!I", header_bytes)[0]
            if msg_length <= 0 or msg_length > MAX_BYTES:
                break

            message_bytes = recv_exact(sock, msg_length)
            if not message_bytes:
                break

            # Decode and display the incoming message
            message = message_bytes.decode("utf-8")
            chat_win.addstr(message + "\n")
            chat_win.refresh()
        except Exception as e:
            chat_win.addstr(f"Error receiving message: {e}\n")
            chat_win.refresh()
            break

def main(stdscr):
    # Enable echo so that characters appear as you type
    curses.echo()
    curses.curs_set(1)
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    # Create a window for chat messages and another for input
    chat_win = curses.newwin(height - 3, width, 0, 0)
    input_win = curses.newwin(3, width, height - 3, 0)
    chat_win.scrollok(True)  # Allow chat window to scroll

    # Setup connection parameters
    host = "127.0.0.1"  # Replace with your server IP if needed
    port = 12345        # Replace with your server port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        chat_win.addstr(f"Connected to server at {host}:{port}\n")
        chat_win.refresh()
    except Exception as e:
        chat_win.addstr(f"Failed to connect: {e}\n")
        chat_win.refresh()
        return

    # Start a thread to receive messages from the server
    threading.Thread(target=receive_messages, args=(chat_win, sock), daemon=True).start()
    
    while True:
        input_win.clear()
        input_win.addstr("Your message: ")
        input_win.refresh()
        
        # Block until the user types a message and presses Enter
        msg = input_win.getstr().decode("utf-8")
        if msg.lower() == "exit":
            break
        
        try:
            # Construct the full message with a label
            full_msg = f"You: {msg}"
            message = Message(full_msg)
            sock.sendall(message.get_data())
            
            # Append the sent message to the chat window immediately
            chat_win.addstr(full_msg + "\n")
            chat_win.refresh()
        except Exception as e:
            chat_win.addstr(f"Error sending message: {e}\n")
            chat_win.refresh()

    sock.close()
    chat_win.addstr("Disconnected from server.\n")
    chat_win.refresh()
    curses.napms(1500)

if __name__ == "__main__":
    curses.wrapper(main)
