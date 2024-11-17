import socket
import re

# References:
# https://www.geeksforgeeks.org/how-to-validate-an-ip-address-using-regex/

USE_LOCALHOST = False # If you want to change this, you should also change it in server.py

def send_srvr_msg(client_socket, message):
    client_socket.send(message.encode())

def start_client():
    # Define the server's IP address and port
    if USE_LOCALHOST:
        server_host = 'localhost'
        server_port = 3000
    else:
        while True:
            server_host = input("Enter the server IP address (Ex: 10.0.0.2): ")
            if re.match("^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$", server_host):
                break
            else:
                print("Invalid input. Please try again.")
        server_port = 5678

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    print("Connected to the server. Listening for messages...")

    while True:
        try:
            # Receive message from the server
            message = client_socket.recv(1024).decode()

            # If no message is received, the server might have closed the connection
            if not message:
                print("Server closed the connection.")
                break

            print(message)

            # Check message prompts
            if "Input your ship of length" in message:
                # Handle user input for ship placement
                while True:
                    placement = input("Enter your ship placement (Format: startrow startcol - endrow endcol, e.g., A5-E5): ") # Change for first move?
                    if re.match("^[A-J][0-9]-[A-J][0-9]$", placement): # Make it so that lower case letters 
                        send_srvr_msg(client_socket, placement)
                        break
                    else:
                        print("Invalid input. Please try again.")
            elif "Input Your Move" in message:
                while True:
                    move = input("Your move (Ex: A1): ")
                    if re.match("^[A-J][0-9]$", move):
                        send_srvr_msg(client_socket, move)
                        break
                    else:
                        print("Invalid input. Please try again.")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break

    # Close the client socket after loop exits
    client_socket.close()
    print("Connection closed.")

if __name__ == "__main__":
    start_client()
