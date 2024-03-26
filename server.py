import threading
import colorama
from style import Style
from time import sleep
from scapy.arch import get_if_addr
from struct import pack
import triviagenerator
import socket
from datetime import datetime, timedelta


class Server:
    def __init__(self, magic_cookie, message_type, server_port, client_port):
        # Initialize class variables
        self.MAGIC_COOKIE = magic_cookie  # Magic cookie for identifying messages
        self.MESSAGE_TYPE = message_type  # Type of message
        self.server_port = server_port  # Port for server
        self.client_port = client_port  # Port for client
        self.ip_address = get_if_addr('Wi-Fi')  # Get IP address of Wi-Fi interface
        self.player_names = []  # Names of players
        self.client_answer = [-1, '']  # Client answers (initially empty)
        self.last_connection_time = None
        self.player_count = 0  # Number of players (initially 0)
        self.server_name = "🕶 CyberQuiz-IntoTheMatrix 🖥"

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
                if self.player_count >= 1 and datetime.now() - self.last_connection_time > timedelta(seconds=5):
                    break

                # Send the message to the client port using UDP broadcast
                sock.sendto(msg, (self.ip_address, self.client_port))

                # Wait for one second before sending the next broadcast
                sleep(1)

    def tcp_client_connect(self, clients):
        # Listen for incoming connections
        self.tcp_socket.listen()
        # Continuously accept clients until there are 2 players connected
        while True:
            if self.player_count >= 1 and datetime.now() - self.last_connection_time > timedelta(seconds=5):
                break
            try:
                # Accept incoming connection from client
                self.tcp_socket.settimeout(10)
                client_socket, (client_ip, client_port) = self.tcp_socket.accept()

                # Add client socket and its address to the list of clients
                clients.append([client_socket, (client_ip, client_port)])
                # Set a timeout for receiving the team name from the client
                client_socket.settimeout(10)
                try:
                    # Receive the player name from the client
                    player_name = str(client_socket.recv(1024), 'utf8')
                    player_name = player_name.rstrip('\n')
                except socket.error as e:
                    # If client doesn't send team name in time, reject it
                    print('Client:', client_ip, 'did not send player name in time.')
                    client_socket.close()
                    clients = clients[:-1]  # Remove the client from the list
                    continue

                # Update player names and count
                self.player_names.append(str(player_name))
                self.player_count += 1
                self.last_connection_time = datetime.now()

                # Print message indicating successful connection
                print(f'{player_name} - successfully connected to the server!')
            except TimeoutError as te:
                continue
            except Exception as e:
                # Print warning message if unable to connect to client
                print('Unable to connect to client - Exception received: ', str(e))
            sleep(0.1)

    def play_game(self, clients):
        question, oracle_answer = triviagenerator.TriviaGenerator().get_question()
        new_msg = f'Welcome to the {self.server_name}  server, where we are answering trivia questions about football.'
        for i in range(self.player_count):
            new_msg += f'\nPlayer {i + 1}: {self.player_names[i]}'
        new_msg += '\n=='
        new_msg += f'\nTrue or false: {question}?\n'

        for client in clients:
            try:
                client[0].sendall(bytes(new_msg, 'utf8'))
            except Exception as e:
                print(Style.FAIL + f"Error sending message to client: {e}" + Style.END_STYLE)
                return False

        mutex = threading.Lock()
        name_index = 0
        for client in clients:
            try:
                threading.Thread(target=self.get_answer,
                                 args=(client[0], self.player_names[name_index], mutex, oracle_answer)).start()
            except Exception as e:
                print(Style.FAIL + f"Error sending message to client: {e}" + Style.END_STYLE)
                return False
            name_index += 1

        init_time = datetime.now()
        i = 0
        while datetime.now() - init_time < timedelta(seconds=10) and self.client_answer == [-1, '']:
            # 10 sec has not passed and correct ans is not being giving
            sleep(1)
            print(f"{10 - i}")
            i += 1

        game_status_msg = 'Expired'
        replay = True
        if self.client_answer[0] == oracle_answer:
            game_status_msg = f" {self.client_answer[1]} is correct! {self.client_answer[1]} wins!" \
                              f"Game over!" \
                              f"\nCongratulations to the winner: {self.client_answer[1]}"
            replay = False
        for client in clients:
            try:
                client[0].send(bytes(game_status_msg, 'utf8'))
            except Exception as e:
                print(Style.FAIL + f"Error sending message to client: {e}" + Style.END_STYLE)
                return False
        return replay

    def get_answer(self, tcp_socket, player_name, mutex, correct_ans):
        client_ans = b''  # Initialize client_ans before the try block
        try:
            client_ans = tcp_socket.recv(1024).decode().strip().upper()  # Receive and decode the answer
            if client_ans in ['1', 'T', 'Y']:
                player_ans = 1  # Treat as True
            elif client_ans in ['0', 'F', 'N']:
                player_ans = 0  # Treat as False
            else:
                raise ValueError("Invalid answer format")
        except ValueError as e:
            print(Style.FAIL + f'{player_name} provided an invalid answer: {client_ans}' + Style.END_STYLE)
            return
        except socket.error as e:
            print(Style.FAIL + f'{player_name} ran out of time!' + Style.END_STYLE)
            return

        mutex.acquire()
        if player_ans == correct_ans and self.client_answer[0] != correct_ans:
            self.client_answer[0] = player_ans
            self.client_answer[1] = player_name
        mutex.release()

    def run_server(self):
        print(self.server_name)
        print(Style.CYAN + f'Server started successfully!' + Style.END_STYLE)

        while True:
            clients = []
            t1 = threading.Thread(target=self.send_udp_offers)
            t2 = threading.Thread(target=self.tcp_client_connect, args=(clients,))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            re = True
            while re:
                re = self.play_game(clients)

            self.client_answer = [-1, '']
            self.player_names = []
            self.player_count = 0

            sleep(2)


if __name__ == '__main__':
    colorama.init()
    server = Server(magic_cookie=0xabcddcba, message_type=0x02, server_port=4567, client_port=1337)
    server.run_server()
