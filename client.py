import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

# Constants
PORT = 5050
SERVER = "localhost"
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.is_connected = False
        self.setup_gui()
        self.client = self.connect_to_server()

        if self.client:
            self.is_connected = True
            self.start_receiving_thread()
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_gui(self):
        """Sets up the GUI components for the chat client."""
        self.root.title("Chat Client")

        # Chat area for incoming messages
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', width=50, height=20)
        self.chat_area.pack(padx=10, pady=10)

        # Entry field for outgoing messages
        self.message_entry = tk.Entry(self.root, width=50)
        self.message_entry.pack(padx=10, pady=5)

        # Send button to send messages
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(padx=10, pady=5)

    def connect_to_server(self):
        """Connects to the server and returns the socket object."""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            self.display_message("[INFO] Connected to the server.")
            return client
        except Exception as e:
            self.display_message(f"[ERROR] Unable to connect to the server: {e}")
            return None

    def start_receiving_thread(self):
        """Starts a background thread to receive messages from the server."""
        receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        receive_thread.start()

    def receive_messages(self):
        """Continuously listens for incoming messages from the server."""
        while self.is_connected:
            try:
                message = self.client.recv(1024).decode(FORMAT)
                if message:
                    self.root.after(0, self.display_message, message)
            except Exception as e:
                self.root.after(0, self.display_message, f"[ERROR] Connection to server lost: {e}")
                self.is_connected = False
                break

    def send_message(self):
        """Sends a message from the client to the server."""
        message = self.message_entry.get()
        if message and self.is_connected:
            try:
                self.client.sendall(message.encode(FORMAT))
                self.message_entry.delete(0, tk.END)
                if message == DISCONNECT_MESSAGE:
                    self.disconnect()
            except Exception as e:
                self.display_message(f"[ERROR] Failed to send message: {e}")

    def display_message(self, message):
        """Displays a message in the chat area."""
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + '\n')
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def disconnect(self):
        """Disconnects from the server and closes the client."""
        if self.is_connected:
            self.is_connected = False
            try:
                self.client.sendall(DISCONNECT_MESSAGE.encode(FORMAT))
                self.client.close()
            except Exception as e:
                self.display_message(f"[ERROR] Error during disconnection: {e}")
        self.root.quit()

    def on_close(self):
        """Handles the window close event to properly disconnect."""
        if self.is_connected:
            self.disconnect()
        self.root.quit()

def start_client():
    """Starts the Chat Client application."""
    root = tk.Tk()
    ChatClient(root)
    root.mainloop()

if __name__ == "__main__":
    start_client()
