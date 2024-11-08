import socket
import threading

# Define the server's IP address and port
SERVER_HOST = 'localhost'
SERVER_PORT = 3000

# This will store the client connections
clients = []

# Function to handle client connections
def handle_client(client_socket, client_number):
    # Send a welcome message with the client's number
    welcome_message = f"You are client {client_number}\n"
    client_socket.send(welcome_message.encode())
    
    # Close the client connection after sending the message
    client_socket.close()

def start_server():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to the server's address and port
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    
    # Start listening for incoming connections
    server_socket.listen(2)
    print("Server is listening on {}:{}".format(SERVER_HOST, SERVER_PORT))
    
    # Keep track of the number of clients that have connected
    client_count = 0
    
    while client_count < 2:  # We only want to allow 2 clients
        # Accept a new client connection
        client_socket, client_addr = server_socket.accept()
        print(f"New connection from {client_addr}")
        
        # Increment client count and assign client number
        client_count += 1
        threading.Thread(target=handle_client, args=(client_socket, client_count)).start()

    # Once 2 clients are connected, close the server socket
    server_socket.close()
    print("Server is shutting down.")

if __name__ == "__main__":
    start_server()