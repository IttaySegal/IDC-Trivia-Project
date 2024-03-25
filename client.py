import socket
from struct import unpack
import msvcrt
import multiprocessing


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

        print("Client started, listening for offer requests...")

        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set socket option to allow reuse of address

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

        print(f'Received offer from server “Mystic” at address 172.1.0.4, attempting to connect...')
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.settimeout(3)

        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(
                f'Failed to connect to server: timed out while connecting with TCP.\nException thrown: {str(e)}')
            self.tcp_socket.close()
            return False

        print(f'Successfully connected to server {self.server_ip}\n')
        player_name_as_bytes = bytes(self.new_player_name, 'utf8')
        self.tcp_socket.sendall(player_name_as_bytes)
        self.tcp_socket.settimeout(None)
        return True

    def get_msg_from_server(self):

        server_msg = str(self.tcp_socket.recv(1024), 'utf8')
        print(server_msg)

    def send_client_answer(self):

        print('Please enter the answer to the trivia: ')
        ans = msvcrt.getch().decode()
        print(f'ans is: {ans}')
        self.tcp_socket.send(bytes(ans, 'utf8'))

    def run_client(self):
        print(f'Client started successfully!')

        while True:
            self.look_for_server()
            success = self.connect_to_server()
            if not success:
                continue
            self.get_msg_from_server()  # Get welcome message and math problem
            t1 = multiprocessing.Process(target=self.send_client_answer)
            t1.start()
            self.get_msg_from_server()  # Get game results
            t1.terminate()

            if self.tcp_socket is not None:
                self.tcp_socket.close()



if __name__ == '__main__':
    client = Client(magic_cookie=0xabcddcba, message_type=0x02, client_port=1337, new_player_name='Shlomi')
    client.run_client()
