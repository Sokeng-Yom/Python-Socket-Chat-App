import threading
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

PORT = 5050
SERVER = "localhost"
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

# Enter your SMTP email configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_email = "your_email@gmail.com"
smtp_password = "your_password"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

clients = {}
clients_info = {}  # Stores client info like name and email
clients_lock = threading.Lock()

def send_email_notification(sender_name, sender_email, recipient_name, recipient_email, message):
    """
    Sends an email notification to the recipient when they receive a message.
    """
    subject = f"New Message from {sender_name}"
    body = f"""
    Hello {recipient_name},

    You have received a new message from {sender_name} ({sender_email}):

    "{message}"

    Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    Regards,
    Chat Server
    """

    msg = MIMEMultipart()
    msg['From'] = smtp_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Send email using SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, recipient_email, msg.as_string())
        server.quit()
        print(Fore.GREEN + f"[EMAIL] Notification sent to {recipient_email}.")
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to send email: {e}")

def broadcast(message, sender_conn=None):
    """
    Send a message to all connected clients except the sender (if applicable).
    """
    with clients_lock:
        for client_conn, client_id in clients.items():
            if client_conn != sender_conn:  # Don't send to the sender
                try:
                    client_conn.sendall(message)
                except Exception as e:
                    print(Fore.RED + f"[ERROR] Failed to send message to {client_id}: {e}")
                    clients.pop(client_conn)

def handle_client(conn, addr):
    """
    Handles each connected client.
    """
    conn.send("Enter your name: ".encode(FORMAT))
    name = conn.recv(1024).decode(FORMAT).strip()

    conn.send("Enter your email: ".encode(FORMAT))
    email = conn.recv(1024).decode(FORMAT).strip()

    with clients_lock:
        clients[conn] = f"{addr}"
        clients_info[conn] = {"name": name, "email": email}

    print(Fore.YELLOW + f"[NEW CONNECTION] {name} ({addr}) connected with email {email}")

    try:
        connected = True
        while connected:
            try:
                msg = conn.recv(1024).decode(FORMAT)
                if not msg:
                    break

                if msg == DISCONNECT_MESSAGE:
                    connected = False

                # Log the message received by the server
                print(Fore.BLUE + f"[{addr}] Received: {msg}")

                # Ensure the message starts with '@'
                if msg.startswith("@"):
                    if ":" in msg:
                        target_client, message = msg[1:].split(":", 1)  # Only split once

                        # Handle @all case
                        if target_client.strip().lower() == "all":
                            # Log the broadcast message
                            print(Fore.CYAN + f"[{addr}] Broadcasting to all clients: {message}")

                            # Broadcast message to all clients
                            broadcast(f"[{clients_info[conn]['name']}] {message}".encode(FORMAT), sender_conn=conn)
                        else:
                            # Send to specific client
                            found = False
                            with clients_lock:
                                for client_conn, client_id in clients.items():
                                    if target_client.strip() in client_id:  # Matching target client
                                        recipient_name = clients_info[client_conn]['name']
                                        recipient_email = clients_info[client_conn]['email']
                                        sender_name = clients_info[conn]['name']
                                        sender_email = clients_info[conn]['email']

                                        print(Fore.GREEN + f"[{addr}] Sending to {recipient_name} ({recipient_email}): {message}")
                                        client_conn.sendall(
                                            f"[{sender_name} -> {recipient_name}] {message}".encode(FORMAT))

                                        # Send email notification
                                        send_email_notification(sender_name, sender_email, recipient_name,
                                                                recipient_email, message)
                                        conn.sendall(f"[SERVER] Email sent to {recipient_name}.".encode(FORMAT))
                                        found = True
                                        break
                            if not found:
                                conn.sendall(Fore.RED + f"[SERVER] Client {target_client} not found.".encode(FORMAT))
                    else:
                        # Invalid format (missing ':')
                        conn.sendall(
                            f"[SERVER] Invalid format. Use '@client_id: message' or '@all: message'.".encode(FORMAT))
                else:
                    # Handle messages that don't follow the '@client_id: message' or '@all: message' format
                    conn.sendall(
                        f"[SERVER] Invalid message format. Use '@client_id: message' or '@all: message'.".encode(FORMAT))

            except ConnectionResetError:
                print(Fore.RED + f"[ERROR] Connection with {addr} was reset.")
                break

    except Exception as e:
        print(Fore.RED + f"[ERROR] Exception in handling client {addr}: {e}")
    finally:
        with clients_lock:
            clients.pop(conn, None)
            clients_info.pop(conn, None)
        conn.close()
        print(Fore.RED + f"[DISCONNECT] {addr} Disconnected")

def server_console():
    """
    Allows server to send messages to all clients.
    Type your message in the server terminal to broadcast it to all clients.
    """
    while True:
        msg = input()
        if msg == 'q':
            break
        broadcast(f"[SERVER] {msg}".encode(FORMAT))

def start():
    print(Fore.GREEN + '[SERVER STARTED]! Listening for connections...')
    server.listen()

    # Start server console for broadcasting messages
    console_thread = threading.Thread(target=server_console, daemon=True)
    console_thread.start()

    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
        except Exception as e:
            print(Fore.RED + f"[ERROR] Exception in accepting connections: {e}")

if __name__ == "__main__":
    try:
        start()
    except Exception as e:
        print(Fore.RED + f"[ERROR] Server encountered an error: {e}")
    finally:
        server.close()
        