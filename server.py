import socket
import threading

# Define the server's IP address and port
SERVER_HOST = 'localhost'
SERVER_PORT = 3000

BOARD_SIZE = 10
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# This will store the client boards (2D arrays)
client_boards = [None, None]  # We have two clients, so initialize with None

# Keep track of the number of clients that have connected
client_count = 0

def send_client_msg(message):
    return message.encode()

# Function to print the board in a readable format
def print_board(board):
    board_str = '  0 1 2 3 4 5 6 7 8 9\n'
    for row in range(BOARD_SIZE):
        board_str += f"{LETTERS[row]} " + " ".join(board[row]) + "\n"
    return board_str

# Function to initialize a board with empty water ('~')
def initialize_board():
    return [['~' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# Function to handle client connections
def handle_client(client_socket, client_number):
    global client_count

    # Send a welcome message with the client's number
    message = f"You are client {client_number}\n"
    client_socket.send(send_client_msg(message))

    if client_count < 2:
        message = "Waiting for other client...\n"
        client_socket.send(send_client_msg(message))
    
    # Wait until both clients are connected
    while client_count < 2:
        pass

    # Both clients are now connected
    message = "Both clients are now connected.\n"
    client_socket.send(send_client_msg(message))

    # Initialize the client's board and store it
    client_boards[client_number] = initialize_board()

    # Send the board to the client
    client_socket.send(send_client_msg(print_board(client_boards[client_number])))

    # This is currently only working for 1 client
    client_socket.send(send_client_msg("Input your ship of length 5\n"))
    print("Input from " + str(client_number) + ":" + client_socket.recv(1024).decode())
    client_socket.send(send_client_msg("Input your ship of length 4\n"))
    print("Input from " + str(client_number) + ":" + client_socket.recv(1024).decode())

    # Close the client connection after the game ends or after sending the final message
    client_socket.close()

def start_server():
    global client_count

    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to the server's address and port
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    
    # Start listening for incoming connections
    server_socket.listen(2)
    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")
    
    while client_count < 2:  # We only want to allow 2 clients
        # Accept a new client connection
        client_socket, client_addr = server_socket.accept()
        print(f"New connection from {client_addr}")
        
        # Assign client number and increment client_count
        client_number = client_count  # Use the current client_count as the client number
        client_count += 1
        
        # Start a new thread to handle the client connection
        threading.Thread(target=handle_client, args=(client_socket, client_number)).start()

    # Once 2 clients are connected, the server continues
    # No need to close the server_socket here unless you plan to shut it down

if __name__ == "__main__":
    start_server()