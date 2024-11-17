import re
import socket
import threading
import time
from urllib.request import urlopen

# References:
# https://www.geeksforgeeks.org/python-program-find-ip-address/

# TODO:
# Try to get this working on multiple hosts

USE_LOCALHOST = False # If you want to change this, you should also change it in client.py
    
# Define server IP and port
if USE_LOCALHOST:
    SERVER_HOST = 'localhost'
    SERVER_PORT = 3000
else:
    SERVER_HOST = re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(str(urlopen('http://checkip.dyndns.com/').read())).group(1) # Get current IP of server
    SERVER_PORT = 5678

BOARD_SIZE = 10
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# Store client boards and track connection
client_boards = [None, None]
move_boards = [None, None]
shipSunk = [
    [False, False, False, False, False],
    [False, False, False, False, False],
]
client_sockets = [None, None]
client_ready = [False, False]
client_count = 0
client_count_lock = threading.Lock()
game_end = False
turn = 0

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
                if board[start_row][col] != '~':
                    print("One or more spot(s) was occupied. Please try again")
                    return False
            
            for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
                board[start_row][col] = str(length)
                
        elif start_col == end_col:  # Vertical placement
            if length != ((max(start_row, end_row) + 1) - min(start_row, end_row)):
                print("Ship was incorrect length. Expected: " + str(length) + " Received: " + str((max(start_row, end_row) + 1) - min(start_row, end_row)))
                return False

            for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
                if board[row][start_col] != '~':
                    print("One or more spot(s) was occupied. Please try again")
                    return False

            for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
                board[row][start_col] = str(length)
                
        else:
            print("Invalid ship placement. Ships must be placed in a straight line.")
            return False
        return True
    except Exception:
        print("Invalid input format.")
        return False

def attemptMove(currentPlayer, inputMove):
    oppBoard = client_boards[getOtherPlayer(currentPlayer)]  # Opponent's board
    move_row, move_col = LETTERS.index(inputMove[0].upper()), int(inputMove[1])

    try:
        if move_boards[currentPlayer][move_row][move_col] == "H" or move_boards[currentPlayer][move_row][move_col] == "M":
            print("Already moved there")
            return False

        if oppBoard[move_row][move_col] != '~':  # It's a hit
            move_boards[currentPlayer][move_row][move_col] = "H"
            oppBoard[move_row][move_col] = "H"
            message = "Hit!"
            # Check if this hit causes any ship to be sunk
            checkForSunkShip(currentPlayer)

            send_client_msg(client_sockets[currentPlayer], message)
            #send_client_msg(client_sockets[getOtherPlayer(currentPlayer)], message)

        else:  # It's a miss
            move_boards[currentPlayer][move_row][move_col] = "M"
            oppBoard[move_row][move_col] = "M"
            send_client_msg(client_sockets[currentPlayer], "Miss!")
        
        return True
    
    except Exception:
        print("Error when attempting move.")
        return False


def checkForSunkShip(currentPlayer):
    oppBoard = client_boards[getOtherPlayer(currentPlayer)]
    shipFound = [False, False, False, False, False]
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if shipFound[4] == False and oppBoard[row][col] == '5':
                shipFound[4] = True
            if shipFound[3] == False and oppBoard[row][col] == '4':
                shipFound[3] = True
            if shipFound[2] == False and oppBoard[row][col] == '3':
                shipFound[2] = True
            if shipFound[1] == False and oppBoard[row][col] == '2':
                shipFound[1] = True
            if shipFound[0] == False and oppBoard[row][col] == '1':
                shipFound[0] = True
        if shipFound[0] and shipFound[1] and shipFound[2] and shipFound[3] and shipFound[4]:
            break
    
    if shipFound[4] == False and shipSunk[getOtherPlayer(currentPlayer)][4] == False:
        shipSunk[getOtherPlayer(currentPlayer)][4] = True
        send_client_msg(client_sockets[currentPlayer], "Ship of Length 5 Sunk!")
    if shipFound[3] == False and shipSunk[getOtherPlayer(currentPlayer)][3] == False:
        shipSunk[getOtherPlayer(currentPlayer)][3] = True
        send_client_msg(client_sockets[currentPlayer], "Ship of Length 4 Sunk!")
    if shipFound[2] == False and shipSunk[getOtherPlayer(currentPlayer)][2] == False:
        shipSunk[getOtherPlayer(currentPlayer)][2] = True
        send_client_msg(client_sockets[currentPlayer], "Ship of Length 3 Sunk!")
    if shipFound[1] == False and shipSunk[getOtherPlayer(currentPlayer)][1] == False:
        shipSunk[getOtherPlayer(currentPlayer)][1] = True
        send_client_msg(client_sockets[currentPlayer], "Ship of Length 2 Sunk!")
    if shipFound[0] == False and shipSunk[getOtherPlayer(currentPlayer)][0] == False:
        shipSunk[getOtherPlayer(currentPlayer)][0] = True
        send_client_msg(client_sockets[currentPlayer], "Ship of Length 1 Sunk!")

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
    global client_count, game_end, turn

    send_client_msg(client_socket, f"You are client {client_number + 1}\n")
    
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

    # Get move from player (main game loop)
    # Make it so that the board is not re-printed every time?
    while True:
        while turn != client_number:
            time.sleep(0.1)

        if game_end:
            send_client_msg("You lose!\n")
            break

        send_client_msg(client_socket, 
            "Your Moves:\n" + 
            print_board(move_boards[client_number]) + 
            "\nYour Board:\n" + 
            print_board(client_boards[client_number]) + 
            "\nInput Your Move\n"
        )
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
                send_client_msg(client_socket, "\nMove unsuccessful, possibly due to you already moving there. Please try again\nInput Your Move")
                move = client_socket.recv(1024).decode()
            if checkForWin(client_number):
                send_client_msg(client_socket, "\nYou win!\n")
                game_end = True
                turn = getOtherPlayer(client_number)
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
