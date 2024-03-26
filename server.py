import threading
from time import sleep
from scapy.arch import get_if_addr
from struct import pack
import trivia_generator
import socket
from datetime import datetime, timedelta
#check github

class Server:
    def __init__(self, magic_cookie, message_type, server_port, client_port):
        self.MAGIC_COOKIE = magic_cookie  # Magic cookie for identifying messages
        self.MESSAGE_TYPE = message_type  # Type of message
        self.server_port = server_port  # Port for server
        self.client_port = client_port  # Port for client
        self.ip_address = get_if_addr('Wi-Fi')  # Get IP address of Wi-Fi interface
        self.player_names = []  # Names of players (initially empty) #changed
        self.client_answer = [-1, '']  # Client answers (initially empty)
        self.last_connection_time = None
        self.player_count = 0  # Number of players (initially 0)

        # Initialize TCP socket for server
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of socket
            self.tcp_socket.bind(('', self.server_port))  # Bind socket to server port
        except socket.error as e:
            # Print error message if initialization fails
            print('Initialization of TCP SOCKET failed. Server initialization failed. Exiting...')
            exit()

    def send_udp_offers(self):


        # Pack the message to be sent
        msg = pack('IbH', self.MAGIC_COOKIE, self.MESSAGE_TYPE, self.server_port)

        # Print the IP address the server is listening on
        print('Listening on IP address', self.ip_address)

        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Set socket option to allow broadcast
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set socket option to allow reuse of address

            # Send UDP offers in broadcast while there are less than 2 clients connected
            while True:
                # Check the condition before entering the inner loop
                if self.player_count >= 1 and datetime.now() - self.last_connection_time > timedelta(seconds=10):
                    print("DB minus1 - UDP_beforeBrake")
                    break

                # Send the message to the client port using UDP broadcast
                sock.sendto(msg, (self.ip_address, self.client_port))

                # Wait for one second before sending the next broadcast
                sleep(1)

    def tcp_client_connect(self, clients):
        self.tcp_socket.listen()
        while True:
            # print(f"{self.player_count}")
            if self.player_count >= 1 and datetime.now() - self.last_connection_time > timedelta(seconds=5):
                print("DB 0 - TCP_beforeBrake")
                break
            print("DB - TCP_tMain")
            try:
                # Accept incoming connection from client
                # print("DB - TCP_t0")
                self.tcp_socket.settimeout(5)
                client_socket, (client_ip, client_port) = self.tcp_socket.accept()
                # print("DB - TCP_t1")

                # Add client socket and its address to the list of clients
                clients.append([client_socket, (client_ip, client_port)])
                # print("DB - TCP_t2")
                # Set a timeout for receiving the team name from the client
                client_socket.settimeout(3)
                # print("DB - TCP_t3")
                try:
                    # Receive the team name from the client
                    player_name = str(client_socket.recv(1024), 'utf8')
                except socket.error as e:
                    # If client doesn't send team name in time, reject it
                    print('Client:', client_ip, 'did not send team name in time.')
                    client_socket.close()
                    clients = clients[:-1]  # Remove the client from the list
                    continue

                # Update player names and count
                self.player_names[self.player_count] = str(player_name)
                self.player_count += 1
                self.last_connection_time = datetime.now()

                # Print message indicating successful connection
                print(player_name, 'successfully connected to the server!')
            except Exception as e:
                # Print warning message if unable to connect to client
                print('Unable to connect to client.\nException received:', str(e))



    def play_game(self, clients):


        question, oracle_answer = trivia_generator.Trivia_generator().get_question()
        msg = f'Welcome to Mystic server where you answer trivia questions.' \
              f'\nPlayer 1: {self.player_names[0]}' \
              f'\nPlayer 2: {self.player_names[1]}' \
              f'\n==' \
              f'\nPlease answer the following question:\n' \
              f'{question}?'
        clients[0][0].settimeout(10)
        clients[1][0].settimeout(10)

        clients[0][0].sendall(bytes(msg, 'utf8'))
        clients[1][0].sendall(bytes(msg, 'utf8'))

        mutex = threading.Lock()
        t1 = threading.Thread(target=self.get_answer, args=(clients[0][0], self.player_names[0], mutex))
        t2 = threading.Thread(target=self.get_answer, args=(clients[1][0], self.player_names[1], mutex))
        t1.start()
        t2.start()

        counter = 0
        while counter < 10 and self.client_answer == [-1, '']:
            counter += 1
            sleep(1)

        if self.client_answer == [-1, '']:
            msg = f"Game over!" \
                  f"\nThe correct answer was {oracle_answer}!" \
                  f"\nNo Winners - Ran out of time!"
        elif self.client_answer[0] == oracle_answer:
            msg = f"Game over!" \
                  f"\nThe correct answer was {oracle_answer}!" \
                  f"\nCongratulations to the winner: {self.client_answer[1]}"
        else:
            msg = f"Game over!" \
                  f"\nThe correct answer was {oracle_answer}!" \
                  f"\nCongratulations to the winner: {self.player_names[0] if self.player_names[1] == self.client_answer[1] else self.player_names[1]}"

        clients[0][0].send(bytes(msg, 'utf8'))
        clients[1][0].send(bytes(msg, 'utf8'))

    def get_answer(self, tcp_socket, team_name, mutex):


        client_ans = b''
        try:
            client_ans = tcp_socket.recv(1024)
            ans = client_ans
        except ValueError as e:
            if len(client_ans) == 0:
                print( f'{team_name} wasn\'t fast enough to answer!')

        except socket.error as e:
            print( f'{team_name} ran out of time!' )
            return

        mutex.acquire()
        if self.client_answer[0] == -1:
            self.client_answer[0] = ans
            self.client_answer[1] = team_name
        mutex.release()

    def run_server(self):


        print( f'Server started successfully!' )

        while True:
            clients = []
            t1 = threading.Thread(target=self.send_udp_offers)
            t2 = threading.Thread(target=self.tcp_client_connect, args=(clients,))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            print("DB1")
            self.play_game(clients)

            self.client_answer = [-1, '']
            self.player_names = ['', '']
            self.player_count = 0


if __name__ == '__main__':
    server = Server(magic_cookie=0xabcddcba, message_type=0x02, server_port=4567, client_port=1337)
    server.run_server()
