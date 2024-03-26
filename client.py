import random
import socket
import colorama
from style import Style
from time import sleep
from struct import unpack
import msvcrt
import multiprocessing
import names


class Client:
    def __init__(self, magic_cookie, message_type, client_port, new_player_name):
        self.server_ip = None
        self.server_port = None
        self.tcp_socket = None

        self.new_player_name = new_player_name
        self.client_port = client_port
        self.MAGIC_COOKIE = magic_cookie
        self.MESSAGE_TYPE = message_type

    def look_for_server(self):
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
            if cookie != self.MAGIC_COOKIE:
                print("Failed to connect to server: UDP packet didn't contain 0xabcddcba in MAGIC COOKIE field.")
                continue

            # Check if MESSAGE TYPE field is correct
            if msg_type != self.MESSAGE_TYPE:
                print("Failed to connect to server: UDP packet didn't contain 0x02 in MESSAGE TYPE field.")
                continue

            # Extract server IP address and port
            self.server_ip = address[0]
            try:
                self.server_port = int(port)
            except ValueError as e:
                print(
                    f"Failed to connect to server: UDP packet didn't contain a number in the port field. Value was: {port}")
                self.server_ip = None
                continue

            # Close the socket and break out of the loop
            sock.close()
            break

    def connect_to_server(self):
        print(Style.CYAN + f'Received offer from {self.server_ip}, attempting to connect...' + Style.END_STYLE)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.settimeout(3)

        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(
                Style.WARNING + f'Failed to connect to server: timed out while connecting with TCP.\nException thrown: {str(e)}' + Style.END_STYLE)
            self.tcp_socket.close()
            return False

        print(Style.CYAN + f'Successfully connected to server {self.server_ip}\n' + Style.END_STYLE)
        player_name_as_bytes = bytes(self.new_player_name+'\n', 'utf8')
        self.tcp_socket.sendall(player_name_as_bytes)
        self.tcp_socket.settimeout(None)
        return True

    def get_msg_from_server(self, color_style):
        try:
            server_msg = self.tcp_socket.recv(1024).decode('utf-8')
            print(color_style + server_msg + Style.END_STYLE)
            if server_msg != 'Expired':
                return False
            return True
        except socket.error as e:
            print("Error receiving message from server:", e)

    def send_client_answer(self):
        try:
            ans = msvcrt.getch().decode()
            print(f'ans is: {ans}')
            self.tcp_socket.send(bytes(ans, 'utf8'))
        except Exception as e:
            print(Style.FAIL + f'Error: {e}' + Style.END_STYLE)

    def run_client(self):
        """
        Summary: This function is used to run all the logic of the client.
        """

        print(Style.CYAN + f'Client started successfully!' + Style.END_STYLE)

        while True:
            self.look_for_server()
            success = self.connect_to_server()
            if not success:
                continue
            replay = True
            while replay:
                self.get_msg_from_server(Style.HEADER)  # Get welcome message and math problem
                t1 = multiprocessing.Process(target=self.send_client_answer)
                t1.start()
                # it the next msg was not received in 1 sec - that means we need to server another round of the game
                # without closing the connection
                replay = self.get_msg_from_server(Style.BLUE)  # Get game results
            t1.terminate()

            if self.tcp_socket is not None:
                self.tcp_socket.close()

            # self.end_session()

            sleep(2)  # Small Delay


if __name__ == '__main__':
    colorama.init()
    player_name = new_player_name=names.get_first_name()
    names = ["Theresa", "Gary", "James",]
    name = random.choice(names)
    client = Client(magic_cookie=0xabcddcba, message_type=0x02, client_port=1337, new_player_name=name)
    client.run_client()


