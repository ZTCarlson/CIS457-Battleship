import socket
import threading
import time

# References:
# https://www.geeksforgeeks.org/python-program-find-ip-address/
# https://github.com/katmfoo/python-client-server

USE_LOCALHOST = False # If you want to change this, you should also change it in client.py
    
# Define server IP and port
if USE_LOCALHOST:
    SERVER_HOST = 'localhost'
    SERVER_PORT = 3000
else:
    SERVER_HOST = socket.gethostbyname(socket.gethostname()) # Get current IP of server
    SERVER_PORT = 5678

# Board constants
BOARD_SIZE = 10
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# Board that clients place their ships
client_boards = [None, None]
# Board of moves tried by clients
move_boards = [None, None]
# List of ships sunk by each client
ship_sunk = [
    [False, False, False, False, False],
    [False, False, False, False, False],
]
# Each client socket
client_sockets = [None, None]
# Check for each client to be ready to start the game (placed all ships)
client_ready = [False, False]
# Number of clients
client_count = 0
# Check to see if the game is over (15 hits by a single client, see check_for_win)
game_end = False
# Current player's move (always starts with the first client to connect)
turn = 0
# Used for server close message to remove duplicates
client_closed = False

# Send a message through the client socket
def send_client_msg(client_socket, message):
    client_socket.send(message.encode())

# Get input from the client
def get_client_msg(client_socket):
    return client_socket.recv(1024).decode()

# Print the client and move boards
def print_board(board):
    board_str = '  0 1 2 3 4 5 6 7 8 9\n'
    for row in range(BOARD_SIZE):
        board_str += str(LETTERS[row]) + " " + " ".join(board[row]) + "\n"
    return board_str

# Fill the board with blank spaces (water)
def initialize_board():
    board = []
    for row in range(BOARD_SIZE):
        board.append([])
        for _ in range(BOARD_SIZE):
            board[row].append("~")
    return board

# Attempt to place the ship on the board
# ship is the input from the player (Ex: A5-E5)
# length is the expected ship length
def put_ship_on_board(ship, player, length):
    try:
        board = client_boards[player] # Get the current board
        start, end = ship.split('-') # Split ship into two parts (Ex: A5-E5 --> start="A5", end="E5")
        # Convert the input into the correct format for the board array (Ex: A5 --> start_row=0, start_col=5)
        # #grabbing the index of the start variable(ex. A) and looking for the index corresponding to it in the "Letters" array
        start_row, start_col = LETTERS.index(start[0]), int(start[1]) 
        end_row, end_col = LETTERS.index(end[0]), int(end[1])

        # Determine if the ship is horizontal or vertical
        if start_row == end_row:  # Horizontal placement (rows are the same, Ex: A0-A4 -> 0 == 0)
            # Iterating over the columns (this is getting the range of the columns it needs to iterate through)
            columns = [min(start_col, end_col), (max(start_col, end_col) + 1)]

            # Check to make sure that the ship is the expected length
            if length != (columns[1] - columns[0]):
                print("Ship was incorrect length. Expected: " + str(length) + " Received: " + str(columns[1] - columns[0]))
                return False

            # Check to see if there's already a ship in the specified location
            for col in range(columns[0], columns[1]):
                if board[start_row][col] != '~': # Not water
                    print("One or more spot(s) was occupied. Please try again")
                    return False
            
            # Place the ship on the board
            for col in range(columns[0], columns[1]):
                board[start_row][col] = str(length)

        elif start_col == end_col:  # Vertical placement (columns are the same, Ex: A5-E5)
            # Iterating over the rows
            rows = [min(start_row, end_row), (max(start_row, end_row) + 1)]
            
            # Check to make sure that the ship is the expected length
            if length != (rows[1] - rows[0]):
                print("Ship was incorrect length. Expected: " + str(length) + " Received: " + str(rows[1] - rows[0]))
                return False
            
            # Check to see if there's already a ship in the specified location
            for row in range(rows[0], rows[1]):
                if board[row][start_col] != '~': # Not water
                    print("One or more spot(s) was occupied. Please try again")
                    return False

            #Place the ship on the board
            for row in range(rows[0], rows[1]):
                board[row][start_col] = str(length)
                
        else: # Diagonal Placement
            print("Invalid ship placement. Ships must be placed in a straight line.")
            return False
        
        return True # Move was valid and ship was placed on the board
    except Exception:
        print("Invalid input format (possibly due to game closing)")
        return False

# Attempt a move (will be invalid if the move is already done by the current player)
#
# Returns an array with two values. The first is whether or not the move went through, 
# and the second is whether it was a hit ("H") or a miss ("M").
#  
# If the move did not go through, the second value will be set to none and the user will 
# be prompted again for a move in the main game loop of handle_client
def attempt_move(current_player, input_move): # ex for input_move A5
    opp_board = client_boards[get_other_player(current_player)]  # Opponent's board(Remember your not changing the value of current_player)
    move_row, move_col = LETTERS.index(input_move[0]), int(input_move[1])

    try:
        # Check if the current player has already moved in the input spot
        if move_boards[current_player][move_row][move_col] == "H" or move_boards[current_player][move_row][move_col] == "M":
            print("Already moved there")
            return [False, None]

        if opp_board[move_row][move_col] != '~':  # It's a hit
            # Update boards
            move_boards[current_player][move_row][move_col] = "H"
            opp_board[move_row][move_col] = "H"

            # Check if this hit causes any ship to be sunk
            check_for_sunk_ship(current_player, opp_board)

            # Inform the client the result of the move
            send_client_msg(client_sockets[current_player], "Hit!\n")
            send_client_msg(client_sockets[get_other_player(current_player)], "You got hit! (" + input_move + ")\n")

            return [True, "H"]
        else:  # It's a miss
            # Update boards
            move_boards[current_player][move_row][move_col] = "M"
            opp_board[move_row][move_col] = "M"

            # Inform the client the result of the move
            send_client_msg(client_sockets[current_player], "Miss!\n")
            send_client_msg(client_sockets[get_other_player(current_player)], "Opponent missed! (" + input_move + ")\n")
            
            return [True, "M"]
    
    except Exception:
        print("Error when attempting move.")
        return [False, None]

# Loop through the opponents board to check if you've sunk one of their ships
# This works by checking for a single number value of each ship length in the opponent's board.
# For example, if the ship of length 3 has not been sunk, there should still be a 3 on the board.
# If the ship of length 3 has been sunk, all of the 3s will be replaced with "H"s
def check_for_sunk_ship(current_player, opp_board):
    ship_found = [False, False, False, False, False]
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            for length in [5, 4, 3, 2, 1]:
                # Early exit check, don't need to check for the length if it is already sunk
                if ship_sunk[get_other_player(current_player)][length-1]:
                    break

                # Found a number on the board, so the ship of that length must not be sunk
                if not ship_found[length-1] and opp_board[row][col] == str(length):
                    ship_found[length-1] = True

        # Early exit check, no need to continue looping if you've found all of the ships
        if ship_found[0] and ship_found[1] and ship_found[2] and ship_found[3] and ship_found[4]:
            break
    
    # If a ship was sunk that was not already detected as sunk, notify the users
    for length in [5, 4, 3, 2, 1]:
        if not ship_found[length-1] and not ship_sunk[get_other_player(current_player)][length-1]:
            ship_sunk[get_other_player(current_player)][length-1] = True
            send_client_msg(client_sockets[current_player], "Ship of Length " + str(length) + " Sunk!")
            send_client_msg(client_sockets[get_other_player(current_player)], "Your Ship of Length " + str(length) + " Was Sunk!")

# Gets the other client number (if current player is 1, other player is 0, and vice versa)
def get_other_player(current_player):
    return 1 - current_player

# Check to see if there are 15 hits by the current player
def check_for_win(current_player):
    hit_count = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if move_boards[current_player][row][col] == "H":
                hit_count += 1
    
    return hit_count == 15

# Handle individual client connection
def handle_client(server_socket, client_socket, client_number):
    global client_count, game_end, turn, client_closed

    try:
        send_client_msg(client_socket, "You are client " + str(client_number + 1) + "\n")
        
        # Initialize the board for the client
        client_boards[client_number] = initialize_board()

        # Collect ship placements as clients connect
        for length in [5, 4, 3, 2, 1]:
            while True:
                prompt = "\nYour board: \n" + print_board(client_boards[client_number]) + "\n"
                prompt += "Input your ship of length " + str(length) + "\n"
                send_client_msg(client_socket, prompt)
                
                # Wait for input from the client
                placement = get_client_msg(client_socket)

                # Attempt to place the ship on the board
                if put_ship_on_board(placement, client_number, length): #(ex. placement == A0-A4)
                    print("Client " + str(client_number + 1) + " placed a ship: " + placement)
                    break
                else:
                    send_client_msg(client_socket, "Invalid placement. Try again.\n")
        
        # Notify client their setup is complete
        send_client_msg(client_socket, "Your ship placements are complete. Waiting for the game to start.\nYour Board:\n" + print_board(client_boards[client_number]))

        # Initialize client move board
        move_boards[client_number] = initialize_board()
        client_ready[client_number] = True

        # Get move from player (main game loop)
        while True:
            # Busy loop to wait for your turn
            while turn != client_number:
                time.sleep(0.1)

            # Check to see if the game is over
            if game_end:
                send_client_msg(client_socket, "You lose!\n")
                break
            
            # Tell the client their boards
            send_client_msg(client_socket, 
                "Your Moves:\n" + 
                print_board(move_boards[client_number]) + 
                "\nYour Board:\n" + 
                print_board(client_boards[client_number]) + 
                "\nInput Your Move\n"
            )

            move = get_client_msg(client_socket)
            
            # Not enough players
            if client_count < 2:
                send_client_msg(client_socket, "Other client has not yet connected.\n")
            # Current player is ready, other player is not
            elif not (client_ready[client_number] and client_ready[get_other_player(client_number)]):
                send_client_msg(client_socket, "Both players are not ready\n")
            # Not the current player's turn (this is old code/a redundant check. Turn is checked above)
            elif turn != client_number:
                send_client_msg(client_socket, "Not your turn yet\n")
            else:
                result = [False, None] 
                # Try the input player move
                while True:
                    result = attempt_move(client_number, move)
                    if result[0]: # If the move was successful
                        break
                    send_client_msg(client_socket, "\nMove unsuccessful, possibly due to you already moving there. Please try again\nInput Your Move")
                    move = get_client_msg(client_socket)
                # Check win condition
                if check_for_win(client_number):
                    send_client_msg(client_socket, "\nYou win!\n")
                    game_end = True
                    turn = get_other_player(client_number)
                    break
                # If the player missed, change the turn
                # If the player hits, they get to go again
                if result[1] == "M": # Change the player turn if the move was a miss
                    turn = get_other_player(client_number)

        # Close the connection once the game is finished
        client_socket.close()
    except Exception: # this exception is for when a client closes the connection before a winner and loser is found
        if not client_closed:
            print("Client " + str(client_number + 1) + " closed the connection. Ending game...")
            client_closed = True
        if client_sockets[get_other_player(client_number)]: # if a socket still exists that is open, it closes it
            client_sockets[get_other_player(client_number)].close()
    if server_socket:
        if game_end:
            print("The Game Has Ended.")
        server_socket.close()

def start_server():
    global client_count

    # Start the sever socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(2)

    # Print server information
    print("Server is listening on " + SERVER_HOST + ":" + str(SERVER_PORT))
    if not USE_LOCALHOST:
        print("Client should connect to: " + SERVER_HOST)
    
    # Start the client sockets
    while True:
        try:
            client_socket, client_addr = server_socket.accept()
        except Exception:
            if server_socket: # This should always be true, but just in case
                server_socket.close()
            print("Server Closed.")
            return
        
        try:
            # Set the global client_sockets variable
            client_sockets[client_count] = client_socket
               
            # Start a thread for each client
            threading.Thread(target=handle_client, args=(server_socket, client_socket, client_count)).start()

            # Increase client count
            client_count += 1

            print("New connection from " + str(client_addr))
        except Exception:
            send_client_msg(client_socket, "Connection failed (possibly due to too many clients)\n")
            client_socket.close()

if __name__ == "__main__":
    start_server()