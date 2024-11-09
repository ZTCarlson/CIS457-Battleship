import socket
import threading

# TODO:
# Start the game/turn logic

# Define server IP and port
SERVER_HOST = 'localhost'
SERVER_PORT = 3000

BOARD_SIZE = 10
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# Store client boards and track connection
client_boards = [None, None]
client_sockets = [None, None]
client_count = 0
client_count_lock = threading.Lock()

def send_client_msg(client_socket, message):
    client_socket.send(message.encode())

def print_board(board):
    board_str = '  0 1 2 3 4 5 6 7 8 9\n'
    for row in range(BOARD_SIZE):
        board_str += f"{LETTERS[row]} " + " ".join(board[row]) + "\n"
    return board_str

def initialize_board():
    return [['~' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# Helper function to place a ship on the board
def putShipOnBoard(ship, board):
    try:
        # Parse start and end points
        start, end = ship.split('-')
        start_row, start_col = LETTERS.index(start[0].upper()), int(start[1])
        end_row, end_col = LETTERS.index(end[0].upper()), int(end[1])

        # Determine if the ship is horizontal or vertical
        if start_row == end_row:  # Horizontal placement
            for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
                board[start_row][col] = 'S'
        elif start_col == end_col:  # Vertical placement
            for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
                board[row][start_col] = 'S'
        else:
            print("Invalid ship placement. Ships must be placed in a straight line.")
            return False
        return True
    except (IndexError, ValueError):
        print("Invalid input format.")
        return False

# Handle individual client connection
def handle_client(client_socket, client_number):
    global client_count

    send_client_msg(client_socket, f"You are client {client_number + 1}\n")

    # Notify client of waiting status if needed
    with client_count_lock:
        if client_count < 2:
            send_client_msg(client_socket, "Waiting for the other client to connect...\n")
    
    # Initialize the board for the client
    client_boards[client_number] = initialize_board()

    # Collect ship placements as clients connect
    for length in [5, 4]:
        while True:
            prompt = "Your board: \n" + print_board(client_boards[client_number]) + "\n"
            prompt += f"Input your ship of length {length}\n"
            send_client_msg(client_socket, prompt)
            
            # Wait for input from the client
            placement = client_socket.recv(1024).decode()
            print(f"Client {client_number + 1} placed a ship: {placement}")

            # Attempt to place the ship on the board
            if putShipOnBoard(placement, client_boards[client_number]):
                break
            else:
                send_client_msg(client_socket, "Invalid placement. Try again.\n")

    # Notify client their setup is complete
    send_client_msg(client_socket, "Your ship placements are complete. Waiting for the game to start.\nYour Board:\n" + print_board(client_boards[client_number]))

    # Close the connection after setup
    client_socket.close()

def start_server():
    global client_count

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(2)
    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_addr = server_socket.accept()
        print(f"New connection from {client_addr}")

        with client_count_lock:
            client_number = client_count
            client_sockets[client_number] = client_socket
            client_count += 1

            # Start a thread for each client
            threading.Thread(target=handle_client, args=(client_socket, client_number)).start()

if __name__ == "__main__":
    start_server()
