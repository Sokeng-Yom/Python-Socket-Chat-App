import threading
import socket
import tkinter as tk
from tkinter import scrolledtext
import datetime

# Constants
PORT = 5050
SERVER = "localhost"
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

class ChatServer:
    def __init__(self, root):
        self.root = root
        self.setup_gui()
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = set()
        self.clients_lock = threading.Lock()
        self.server_running = False

        self.bind_server()

    def setup_gui(self):
        """Sets up the GUI components."""
        self.root.title("Chat Server")

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', width=50, height=20)
        self.log_area.pack(padx=10, pady=10)

        self.message_entry = tk.Entry(self.root, width=50)
        self.message_entry.pack(padx=10, pady=5)

        self.send_button = tk.Button(self.root, text="Broadcast", command=self.server_broadcast)
        self.send_button.pack(padx=10, pady=5)

        self.start_button = tk.Button(self.root, text="Start Server", command=self.start_server)
        self.start_button.pack(padx=10, pady=5)

        self.stop_button = tk.Button(self.root, text="Stop Server", command=self.stop_server, state='disabled')
        self.stop_button.pack(padx=10, pady=10)

    def bind_server(self):
        """Binds the server to the address."""
        try:
            self.server.bind(ADDR)
        except Exception as e:
            self.log_message(f"[ERROR] Could not bind server: {e}")

    def log_message(self, message):
        """Logs a message in the GUI."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + '\n')
        self.log_area.config(state='disabled')
        self.log_area.yview(tk.END)

    def handle_client(self, conn, addr):
        """Handles communication with a client."""
        self.log_message(f"[NEW CONNECTION] {addr} connected.")
        connected = True

        while connected:
            try:
                msg = conn.recv(1024).decode(FORMAT)
                if msg == DISCONNECT_MESSAGE:
                    connected = False
                elif msg:
                    broadcast_message = self.format_message(addr, msg)
                    self.log_message(broadcast_message)
                    self.broadcast(broadcast_message, conn)
            except (ConnectionResetError, Exception) as e:
                self.log_message(f"[ERROR] Connection issue with {addr}: {e}")
                break
        
        self.remove_client(conn)
        conn.close()
        self.log_message(f"[DISCONNECT] {addr} disconnected")

    def format_message(self, addr, msg):
        """Formats the message with a timestamp and address."""
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{time} [{addr}] {msg}"

    def server_broadcast(self):
        """Broadcasts a server message to all clients."""
        message = self.message_entry.get()
        if message:
            broadcast_message = f"{self.format_message('SERVER', message)}"
            self.message_entry.delete(0, tk.END)
            self.log_message(f"[BROADCAST] {broadcast_message}")
            self.broadcast(broadcast_message)

    def broadcast(self, message, sender_conn=None):
        """Sends a message to all clients except the sender."""
        with self.clients_lock:
            for client in self.clients:
                if client != sender_conn:
                    try:
                        client.sendall(message.encode(FORMAT))
                    except Exception as e:
                        self.log_message(f"[ERROR] Error broadcasting to client: {e}")

    def remove_client(self, conn):
        """Removes a client from the set of clients."""
        with self.clients_lock:
            if conn in self.clients:
                self.clients.remove(conn)

    def start_server(self):
        """Starts the server and accepts clients."""
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.server_running = True
        self.log_message('[SERVER STARTED]')
        
        self.server.listen()
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        """Accepts incoming client connections."""
        while self.server_running:
            try:
                conn, addr = self.server.accept()
                with self.clients_lock:
                    self.clients.add(conn)
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except Exception as e:
                self.log_message(f"[ERROR] Error accepting client: {e}")
                break

    def stop_server(self):
        """Stops the server and disconnects all clients."""
        self.server_running = False
        self.log_message('[SERVER STOPPING]')

        with self.clients_lock:
            for client in self.clients:
                try:
                    client.sendall(DISCONNECT_MESSAGE.encode(FORMAT))
                    client.close()
                except Exception as e:
                    self.log_message(f"[ERROR] Error disconnecting client: {e}")
            self.clients.clear()

        self.server.close()
        self.stop_button.config(state='disabled')
        self.start_button.config(state='normal')
        self.log_message('[SERVER STOPPED]')

def start_server_gui():
    """Launches the GUI."""
    root = tk.Tk()
    ChatServer(root)
    root.mainloop()

if __name__ == "__main__":
    start_server_gui()
