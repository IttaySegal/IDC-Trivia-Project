import random
import socket
import colorama
from style import Style
from time import sleep
from struct import unpack
import msvcrt
import multiprocessing

"""
A Client class for connecting to a game server. It listens for UDP broadcast messages from the server,
establishes a TCP connection, and engages in a Q&A game. The class handles searching for the server,
connecting, sending player responses, and receiving messages.
"""


class Client:
    def __init__(self, magic_cookie, message_type, client_port, new_player_name):
        """
        Initializes the client with specific game and network parameters.

        Parameters:
        - magic_cookie (byte): The magic cookie value to look for in server broadcasts.
        - message_type (int): The message type to validate in server broadcasts.
        - client_port (int): The port on which the client listens for server broadcasts.
        - new_player_name (str): The player's name to use when connecting to the game server.
        """

        self.server_ip = None
        self.server_port = None
        self.tcp_socket = None

        self.new_player_name = new_player_name
        self.client_port = client_port
        self.magic_cookie = magic_cookie
        self.message_type = message_type

    def look_for_server(self):
        """
        Listens for server broadcast messages over UDP, validates them, and extracts the server IP and port for TCP
        connection.
        """

        # Print message indicating listening for offer requests
        print("Listening for offer requests...")

        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set socket option to allow reuse of address

        # Bind the socket to the client port
        sock.bind(('', self.client_port))

        while True:
            # Receive data and address from UDP packet
            data, address = sock.recvfrom(1024)

            try:
                # Unpack received data to extract fields
                cookie, msg_type, port = unpack('IbH', data)
                cookie, msg_type = int(hex(cookie), 16), int(hex(msg_type), 16)
            except Exception as e:
                # Print warning message if UDP packet is not in the right format
                print("Failed to connect to server: UDP packet wasn't in the the right format.")
                continue

            # Check if MAGIC COOKIE field is correct
            if cookie != self.magic_cookie:
                print("Failed to connect to server: UDP packet didn't contain 0xabcddcba in MAGIC COOKIE field.")
                continue

            # Check if MESSAGE TYPE field is correct
            if msg_type != self.message_type:
                print("Failed to connect to server: UDP packet didn't contain 0x02 in MESSAGE TYPE field.")
                continue

            # Extract server IP address and port
            self.server_ip = address[0]
            try:
                self.server_port = int(port)
            except ValueError as e:
                print(
                    f"Failure: UDP packet didn't contain a number in the port field. Value was: {port}")
                self.server_ip = None
                continue

            # Close the socket and break out of the loop
            sock.close()
            break

    def connect_to_server(self):
        """
        Attempts to establish a TCP connection with the server using the IP and port discovered in the UDP broadcast.

        Returns:
        True if the connection was successful, False otherwise.
        """

        print(Style.CYAN + f'Received offer from {self.server_ip}, attempting to connect...' + Style.END_STYLE)
        # set the tcp socket ready for connection to the server
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.settimeout(3)
        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(Style.WARNING + f'Failure: time out when connecting with TCP.\nException thrown: {str(e)}' + Style.END_STYLE)
            self.tcp_socket.close()
            return False

        print(Style.CYAN + f'Successfully connected to server {self.server_ip}\n' + Style.END_STYLE)
        player_name_as_bytes = (self.new_player_name + '\n')
        # sends the name of the player to the server
        self.tcp_socket.sendall(player_name_as_bytes.encode())
        self.tcp_socket.settimeout(None)
        return True

    def get_msg_from_server(self, color_style):
        """
        Receives a message from the server and prints it in a specified color style.

        Parameters:
        - color_style (Style): The style to apply to the printed message.

        Returns:
        False if the message received is not 'Expired', True otherwise.
        """

        # the message that the server sends to client if we don't
        # terminate the connection (meaning there is another round of questions
        server_msg_another_round = 'Expired'
        try:
            server_msg = self.tcp_socket.recv(1024).decode('utf8')
            print(color_style + server_msg + Style.END_STYLE)
            if server_msg != server_msg_another_round:
                return False
            return True
        except socket.error as e:
            print("Error receiving message from server:", e)

    def send_client_answer(self):
        """
        Gets an answer from the client via keyboard input and sends it to the server.
        """
        while True:
            try:
                ans = msvcrt.getch().decode()
                print(f'client {self.new_player_name} answer is: {ans}')
                self.tcp_socket.send(ans.encode())
            except socket.error as e:
                if isinstance(e, KeyboardInterrupt):
                    print(Style.FAIL + "Keyboard interrupt detected." + Style.END_STYLE)
                elif isinstance(e, ConnectionAbortedError):
                    print(Style.FAIL + "The connection was aborted by the host machine." + Style.END_STYLE)
                elif isinstance(e, ConnectionResetError):
                    print(Style.FAIL + "The connection was reset by the peer." + Style.END_STYLE)
                elif isinstance(e, OSError):
                    print(Style.FAIL + f"An OS error occurred: {e.errno} - {e.strerror}" + Style.END_STYLE)
                else:
                    print(Style.FAIL + f"A socket error occurred: {e}" + Style.END_STYLE)
            except Exception as e:
                print(Style.FAIL + f'Error: {e}' + Style.END_STYLE)

    def run_client(self):
        """
        Main client function that orchestrates the process of looking for a server, connecting, and handling trivia.
        """

        print(Style.CYAN + f'Client started successfully!' + Style.END_STYLE)

        while True:
            self.look_for_server()
            success = self.connect_to_server()
            if not success:
                continue
            replay = True
            self.get_msg_from_server(Style.HEADER)
            # entering the loop to play the game
            while replay:
                self.get_msg_from_server(Style.HEADER)  # Get welcome message and math problem
                t1 = multiprocessing.Process(target=self.send_client_answer)
                t1.start()
                replay = self.get_msg_from_server(Style.BLUE)  # Get game results
                t1.terminate() # terminating the connection
            t1.terminate()

            if self.tcp_socket is not None:
                self.tcp_socket.close()

            sleep(1)  # Small Delay


if __name__ == '__main__':
    # initiate the Style
    colorama.init()
    # list of names for the players
    names = [
    "Alex", "Jordan", "Taylor", "Jamie", "Casey", "Morgan", "Riley", "Cameron", "Avery",
    "Quinn", "Sam", "Dakota", "Parker", "Peyton", "Skylar", "Drew", "Blake", "Charlie",
    "Bailey", "Reese", "Hayden", "Rowan", "Kendall", "Finley", "Marley", "Harley", "River",
    "Phoenix", "Sage", "Shiloh", "Ellis", "Arden", "Emerson", "Reagan", "Lennon", "Oakley",
    "Sawyer", "Jaden", "Micah", "Devon", "Spencer", "Case", "Skyler", "Brooklyn", "Rory",
    "Hunter", "Payton", "Dylan", "Elliot", "Harper"
    ]
    family_names = [
        "Anderson", "Bennett", "Carter", "Davidson", "Edwards", "Foster", "Graham", "Harris",
        "Irwin", "Jones", "Kingston", "Lambert", "Murray", "Norton", "Owens", "Patterson",
        "Quinn", "Richardson", "Smith", "Taylor", "Underwood", "Vaughn", "Wallace", "Xavier",
        "Young", "Zimmerman", "Allen", "Black", "Clark", "Davis", "Evans", "Ford", "Green",
        "Hill", "Ingram", "Johnson", "Knight", "Lee", "Miller", "Nolan", "Ortega", "Phillips",
        "Quincy", "Roberts", "Stevens", "Thomas", "Upton", "Vance", "Wells", "York"
    ]

    name = random.choice(names) + " " + random.choice(family_names)  # Decreases the chance for double names
    client = Client(magic_cookie=0xabcddcba, message_type=0x02, client_port=13117, new_player_name=name)
    client.run_client()
