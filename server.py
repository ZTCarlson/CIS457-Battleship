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
move_boards = [None, None]
ship_placements = [
    {"5": [], "4": [], "3": [], "2": [], "1": []},
    {"5": [], "4": [], "3": [], "2": [], "1": []}
]
client_sockets = [None, None]
client_ready = [False, False]
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
def putShipOnBoard(ship, player, length):
    try:
        # Parse start and end points
        board = client_boards[player]
        start, end = ship.split('-')
        start_row, start_col = LETTERS.index(start[0].upper()), int(start[1])
        end_row, end_col = LETTERS.index(end[0].upper()), int(end[1])

        # Determine if the ship is horizontal or vertical
        if start_row == end_row:  # Horizontal placement
            if length != ((max(start_col, end_col) + 1) - min(start_col, end_col)):
                print("Ship was incorrect length. Expected: " + str(length) + " Received: " + str((max(start_col, end_col) + 1) - min(start_col, end_col)))
                return False

            # Check to see if there's already a ship in the specified location
            for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
                if board[start_row][col] == 'S':
                    print("One or more spot(s) was occupied. Please try again")
                    return False
            
            for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
                board[start_row][col] = 'S'
                ship_placements[player][str(length)] += [start_row, col]
        elif start_col == end_col:  # Vertical placement
            if length != ((max(start_row, end_row) + 1) - min(start_row, end_row)):
                print("Ship was incorrect length. Expected: " + str(length) + " Received: " + str((max(start_row, end_row) + 1) - min(start_row, end_row)))
                return False

            for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
                if board[row][start_col] == 'S':
                    print("One or more spot(s) was occupied. Please try again")
                    return False

            for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
                board[row][start_col] = 'S'
                ship_placements[player][str(length)] += [row, start_col]
        else:
            print("Invalid ship placement. Ships must be placed in a straight line.")
            return False
        return True
    except Exception:
        print("Invalid input format.")
        return False

# This is not working for some reason
def attemptMove(currentPlayer, inputMove):
    oppBoard = client_boards[getOtherPlayer(currentPlayer)]  # Opponent's board
    move_row, move_col = LETTERS.index(inputMove[0].upper()), int(inputMove[1])

    try:
        if move_boards[currentPlayer][move_row][move_col] == "H" or move_boards[currentPlayer][move_row][move_col] == "M":
            print("Already moved there")
            return False

        if oppBoard[move_row][move_col] == 'S':  # It's a hit
            move_boards[currentPlayer][move_row][move_col] = "H"
            message = "Hit!"
            # Check if this hit causes any ship to be sunk
            sunk_ship = checkForSunkShip(currentPlayer, move_row, move_col)
            if sunk_ship:
                message += f" You sunk the opponent's {sunk_ship} ship!"

            send_client_msg(client_sockets[currentPlayer], message)
            send_client_msg(client_sockets[getOtherPlayer(currentPlayer)], message)

        else:  # It's a miss
            move_boards[currentPlayer][move_row][move_col] = "M"
            send_client_msg(client_sockets[currentPlayer], "Miss!")
        
        return True

    except Exception:
        print("Error when attempting move.")
        return False


def checkForSunkShip(currentPlayer, hit_row, hit_col):
    # Loop through each ship length in ship_placements
    for ship_length, positions in ship_placements[getOtherPlayer(currentPlayer)].items():
        # Extract the ship's positions
        ship_positions = [(positions[i], positions[i+1]) for i in range(0, len(positions), 2)]
        
        # Check if the current hit is part of this ship
        if (hit_row, hit_col) in ship_positions:
            # Check if all positions of this ship have been hit
            all_hit = True
            for (row, col) in ship_positions:
                if move_boards[currentPlayer][row][col] != "H":
                    all_hit = False
                    break

            if all_hit:
                # If all parts of the ship are hit, the ship is sunk
                return f"{ship_length}-unit"  # Return the size of the sunk ship (e.g., "5-unit")
    
    return None  # If no ship was sunk, return None

def getOtherPlayer(currentPlayer):
    if currentPlayer == 1:
        return 0
    else:
        return 1

def checkForWin(currentPlayer):
    hit_count = 0
    
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if move_boards[currentPlayer][row][col] == "H":
                hit_count += 1
    
    if hit_count == 15:
        return True
    else:
        return False

# Handle individual client connection
def handle_client(client_socket, client_number):
    global client_count

    send_client_msg(client_socket, f"You are client {client_number + 1}\n")

    # Notify client of waiting status if needed
    #with client_count_lock:
    #    if client_count < 2:
    #        send_client_msg(client_socket, "Waiting for the other client to connect...\n")
    
    # Initialize the board for the client
    client_boards[client_number] = initialize_board()

    # Collect ship placements as clients connect
    for length in [5, 4, 3, 2, 1]:
        while True:
            prompt = "\nYour board: \n" + print_board(client_boards[client_number]) + "\n"
            prompt += f"Input your ship of length {length}\n"
            send_client_msg(client_socket, prompt)
            
            # Wait for input from the client
            placement = client_socket.recv(1024).decode()

            # Attempt to place the ship on the board
            if putShipOnBoard(placement, client_number, length):
                print(f"Client {client_number + 1} placed a ship: {placement}")
                break
            else:
                send_client_msg(client_socket, "Invalid placement. Try again.\n")
    
    # Notify client their setup is complete
    send_client_msg(client_socket, "Your ship placements are complete. Waiting for the game to start.\nYour Board:\n" + print_board(client_boards[client_number]))

    # Initialize client move board
    move_boards[client_number] = initialize_board()
    client_ready[client_number] = True

    turn = 0
    lost = False
    # Get move from player (main game loop)
    while True:
        if lost:
            send_client_msg("You lose!\n")
            break

        send_client_msg(client_socket, "Input Your Move\n") # Add sending the boards
        move = client_socket.recv(1024).decode()
        
        if client_count < 2:
            send_client_msg(client_socket, "Other client has not yet connected.\n")
        elif not (client_ready[client_number] and client_ready[getOtherPlayer(client_number)]):
            send_client_msg(client_socket, "Both players are not ready")
        elif turn != client_number:
            send_client_msg(client_socket, "Not your turn yet\n")
        else:
            while True:
                if attemptMove(client_number, move):
                    break
            if checkForWin(client_number):
                send_client_msg(client_socket, "You win!\n")
                break
            turn = getOtherPlayer(client_number) # add: Do not change the turn if you got a hit

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
