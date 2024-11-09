import socket
import re

# Define the server's IP address and port
SERVER_HOST = 'localhost'
SERVER_PORT = 3000

def send_srvr_msg(message):
    return message.encode()

def start_client():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect to the server
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    print("Connected to the server. Listening for messages...")

    while True:
        try:
            # Receive a message from the server
            message = client_socket.recv(1024).decode()

            # If there's no message, break out of the loop (server may have closed connection)
            if not message:
                print("Server closed the connection.")
                break

            print("Received message:", message)

            if message == "Input your ship of length 5\n" or message == "Input your ship of length 4\n":
                while True:
                    placement = input("Your placement (Format: startrow startcol - endrow endcol, Ex: A5-E5): ")
                    if re.match("^[A-J][0-9]-[A-J][0-9]$", placement):
                        client_socket.send(send_srvr_msg(placement))
                        break
                    else:
                        print("Invalid input. Please try again\n")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    
    # Close the client socket after exiting the loop
    client_socket.close()
    print("Connection closed.")

if __name__ == "__main__":
    start_client()