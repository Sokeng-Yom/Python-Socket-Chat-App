import socket
import threading
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

PORT = 5050
SERVER = "localhost"
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"


def receive_messages(client):
    """
    Listen to messages from the server in a separate thread.
    """
    while True:
        try:
            msg = client.recv(1024).decode(FORMAT)
            if not msg:
                break
            print(Fore.CYAN + msg)  # Colorize received messages
        except Exception as e:
            print(Fore.RED + f"[ERROR] Failed to receive message: {e}")
            break


def connect():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(ADDR)
        print(Fore.GREEN + "[SUCCESS] Connected to server.")
        return client
    except Exception as e:
        print(Fore.RED + f"[ERROR] Could not connect to server: {e}")
        return None


def send(client, msg):
    """
    Send a message to the server.
    
    - To broadcast a message to all clients, use the format: '@all: your message'
    - To send a message to a specific client, use the format: '@client_id: your message'
      (where 'client_id' is the address of the client, such as '127.0.0.1:5051')
    """
    try:
        message = msg.encode(FORMAT)
        client.send(message)
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to send message: {e}")


def start():
    answer = input(Fore.YELLOW + 'Would you like to connect (yes/no)? ')
    if answer.lower() != 'yes':
        return

    connection = connect()
    if not connection:
        return

    # Prompt the user for their name
    name = input(Fore.YELLOW + "Enter your name: ")
    while not name.strip():  # Ensure the name is not empty
        name = input(Fore.RED + "Name cannot be empty. Please enter your name: ")

    # Prompt the user for their email
    email = input(Fore.YELLOW + "Enter your email: ")
    while not email.strip():  # Ensure the email is not empty
        email = input(Fore.RED + "Email cannot be empty. Please enter your email: ")

    # Send name and email to the server
    send(connection, name)
    send(connection, email)

    # Start receiving messages in a separate thread
    threading.Thread(target=receive_messages, args=(connection,), daemon=True).start()

    print(Fore.GREEN + "Instructions for sending messages:"+ 
          "\n- To broadcast to all clients: @all: message"+
          "\n- To send to a specific client: @client_id: message (e.g., @127.0.0.1:5051: Hello)"+ 
          "\n- Type 'q' to disconnect")

    while True:
        msg = input(Fore.YELLOW + "Message (q for quit, @all: for broadcast): ")

        if msg == 'q':
            break

        send(connection, msg)

    send(connection, DISCONNECT_MESSAGE)
    print(Fore.RED + 'Disconnected')
    connection.close()  # Close the socket


if __name__ == "__main__":
    start()