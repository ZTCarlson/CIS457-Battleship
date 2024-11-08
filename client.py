import socket

# Define the server's IP address and port
SERVER_HOST = 'localhost'
SERVER_PORT = 3000

def start_client():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect to the server
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    # Receive the welcome message from the server
    message = client_socket.recv(1024).decode()
    print(message)  # Print the message from the server
    
    # Close the client socket
    client_socket.close()

if __name__ == "__main__":
    start_client()