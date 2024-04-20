import threading
import colorama
from style import Style
from time import sleep
from scapy.arch import get_if_addr
from struct import pack
import trivia_generator
import socket
from datetime import datetime, timedelta

"""
A Server class for hosting a trivia game. It broadcasts UDP messages to clients, accepts TCP connections,
and conducts a Q&A game with connected clients. The class handles sending UDP offers, accepting TCP client connections,
processing player responses, and managing gameplay.
"""

class Server:
    WIFI_INTERFACE = 'Wi-Fi'  # Default Wi-Fi interface name
    SERVER_NAME = "🕶 CyberQuiz-IntoTheMatrix🖥"  # Default server name

    def __init__(self, magic_cookie, message_type, server_port, client_port, wifi_interface=None, server_name=None):
        """
        Initializes the Server class.
        param:
            magic_cookie (byte): Magic cookie for identifying messages.
            message_type (byte): Type of message.
            server_port (int): Port for server.
            client_port (int): Port for client.
            wifi_interface (str, optional): Name of the Wi-Fi interface. Defaults to None.
            server_name (str, optional): Name of the server. Defaults to None.
        """
        # Initialize class variables
        self.magic_cookie = magic_cookie  # Magic cookie for identifying messages
        self.message_type = message_type  # Type of message
        self.server_port = server_port  # Port for server
        self.client_port = client_port  # Port for client
        self.ip_address = get_if_addr(wifi_interface or Server.WIFI_INTERFACE)  # Get IP address of Wi-Fi interface
        self.server_name = server_name or Server.SERVER_NAME  # Set server name
        self.player_names = []  # Names of players
        self.last_connection_time = None
        self.player_count = 0  # Number of players (initially 0)
        self.final_answer = [-1, '']  # Client answers (initially empty)
        self.remaining_time = 10
        self.clients = []

        # Initialize TCP socket for server
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of socket
            self.tcp_socket.bind(('', self.server_port))  # Bind socket to server port
        except socket.error as e:
            # Print error message if initialization fails
            print(Style.FAIL + 'Initialization of TCP SOCKET failed. Server initialization failed. Exiting...' + Style.END_STYLE)
            exit()

    def send_udp_offers(self):
        """
        Send UDP offers in broadcast while there are less than 2 clients connected.
        """
        # Pack the message to be sent
        msg = pack('IbH', self.magic_cookie, self.message_type, self.server_port)

        # Print the IP address the server is listening on
        print('Listening on IP address', self.ip_address)

        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Set socket option to allow broadcast
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set socket option to allow reuse of address

            # Send UDP offers in broadcast while there are less than 1 client connected
            while True:
                # Check the condition before entering the inner loop
                if self.player_count >= 1 and datetime.now() - self.last_connection_time > timedelta(seconds=10):
                    break

                # Send (broadcast) the message to the clients ports using UDP broadcast
                sock.sendto(msg, ('<broadcast>', self.client_port))

                # Wait for one second before sending the next broadcast
                sleep(1)

    def tcp_client_connect(self):
        """
        Listen for incoming TCP connections from clients and accept them.
        Note:
            This method continuously accepts clients until there is at least 1 player and no more players connected in the last 10 seconds.
        """
        # Listen for incoming connections
        self.tcp_socket.listen()

        # Continuously accept clients until conditions are met
        while True:
            if self.player_count >= 1 and datetime.now() - self.last_connection_time > timedelta(seconds=10):
                break
            try:
                # Accept incoming connection from client
                self.tcp_socket.settimeout(10)
                client_socket, (client_ip, client_port) = self.tcp_socket.accept()

                # Add client socket and its address to the list of clients
                is_active = True
                self.clients.append([client_socket, is_active, (client_ip, client_port)])

                # Set a timeout for receiving the player name from the client
                try:
                    # Receive the player name from the client
                    player_name = str(client_socket.recv(1024), 'utf8')
                    player_name = player_name.rstrip('\n')
                except socket.error as e:
                    # If client doesn't send player name in time, reject it
                    print(Style.FAIL + 'Client:', client_ip, 'did not send player name in time.' + Style.END_STYLE)
                    client_socket.close()
                    self.clients.pop()  # Remove the client from the list
                    continue

                # Update player names and count
                self.player_names.append(str(player_name))
                self.player_count += 1
                self.last_connection_time = datetime.now()

                # Print message indicating successful connection
                print(Style.CYAN + f'{player_name} - successfully connected to the server!' + Style.END_STYLE)
            except TimeoutError as te:
                continue
            except Exception as e:
                # Print warning message if unable to connect to client
                print(Style.FAIL + f'Unable to connect to client - Exception received: {e}' + Style.END_STYLE)
                return
            sleep(0.1) #was 0.1

    def build_welcome_message(self):
        """
        This function constructs a welcome message for the trivia game server,
        including the server name, a brief description, the list of player names,
        and a visual separator.
        Returns:
            str: The constructed welcome message.
        """
        welcome_msg = f'Welcome to the {self.server_name} server, where we answer trivia questions.\n'
        welcome_msg += '\n'.join([f'Player {i + 1}: {name}' for i, name in enumerate(self.player_names)])
        welcome_msg += '\n=='
        print(Style.HEADER + f'{welcome_msg}' + Style.END_STYLE)
        return welcome_msg

    def send_welcome_message(self, client, welcome_msg, player_name):
        """
        This function sends a welcome message to a client socket. If sending fails due to a TimeoutError,
        ConnectionResetError, or any other exception, appropriate actions are taken, such as updating the
        player count or closing the client socket.
        Args:
            client : A tuple containing the client socket and a boolean indicating if the client is active.
            welcome_msg (str): The welcome message to send to the client.
            player_name (str): player_name
        """
        if not client[1]:
            # print(Style.WARNING + f'send_welcome_message-Inactive Client: {player_name}' + Style.END_STYLE)
            return
        client_socket = client[0]
        try:
            client_socket.sendall(welcome_msg.encode())
        except TimeoutError as te:
            print(Style.FAIL + f'welcome_message-TimeoutError: {te}' + Style.END_STYLE)
            self.player_count -= 1
            return
        except ConnectionResetError as cre:
            print(Style.FAIL + f'welcome_message-ConnectionResetError: {cre}' + Style.END_STYLE)
            self.player_count -= 1
            client[1] = False
            client_socket.close()
            return
        except Exception as e:
            print(Style.FAIL + f'welcome_message-Exception: {e}' + Style.END_STYLE)
            self.player_count -= 1
            return

    def send_question(self, client, player_name, trivia_question):
        """
        This function sends a trivia question to a client socket. If the client is inactive,
        a warning message is printed. If sending fails due to a TimeoutError, ConnectionResetError,
        or any other exception, appropriate actions are taken, such as updating the player count or
        closing the client socket.
        Args:
            client: An array containing the client socket and a boolean indicating if the client is active.
            player_name (str): The name of the player associated with the client socket.
            trivia_question (str): The trivia question to send to the client.
        """
        if not client[1]:
            # print(Style.WARNING + f'send_question-Inactive Client: {player_name}' + Style.END_STYLE)
            return
        client_socket = client[0]
        try:
            client_socket.sendall(trivia_question.encode())
        except TimeoutError as te:
            print(Style.FAIL + f'send_question-send_question-TimeoutError: {te}' + Style.END_STYLE)
        except ConnectionResetError as cre:
            print(Style.FAIL + f'send_question-ConnectionResetError: {cre}' + Style.END_STYLE)
            self.player_count -= 1
            client[1] = False
            client_socket.close()
        except Exception as e:
            print(Style.FAIL + f'send_question-Exception: {e}' + Style.END_STYLE)

    def send_game_status(self, client, player_name, status_msg):
        """
        This function sends a game status message to a client socket. If the client is inactive,
        a warning message is printed. If sending fails due to a TimeoutError or ConnectionResetError,
        appropriate actions are taken, such as closing the client socket or updating the player count.
        Any other exceptions raised during sending are propagated up as a socket timeout exception.
        Args:
            client (tuple): A tuple containing the client socket and a boolean indicating if the client is active.
            player_name (str): The name of the player associated with the client socket.
            status_msg (str): The game status message to send to the client.
        Raises:
            socket.timeout: If an unexpected exception occurs during sending, it is raised as a socket timeout exception.
        """
        if not client[1]:
            # print(Style.WARNING + f'send_game_status-Inactive Client: {player_name}' + Style.END_STYLE)
            return
        client_socket = client[0]
        try:
            client_socket.sendall(status_msg.encode())
        except TimeoutError as te:
            print(Style.FAIL + f'send_game_status-TimeoutError: {te}' + Style.END_STYLE)
            client_socket.close()
        except ConnectionResetError as cre:
            print(Style.FAIL + f'send_game_status-ConnectionResetError: {cre}' + Style.END_STYLE)
            self.player_count -= 1
            client[1] = False
            client_socket.close()
        except Exception as e:
            raise socket.timeout(f"send_game_status-Exception: {e}")

    def flush_garbage(self, client, player_name):
        """
        This method reads and discards any remaining data in the client socket buffer.
        Args:
            client (tuple): A tuple containing the client socket and a boolean indicating if the client is active.
            player_name
        """
        if not client[1]:
            # print(Style.WARNING + f'flush_garbage-Inactive Client: {player_name}' + Style.END_STYLE)
            return
        tcp_socket = client[0]
        tcp_socket.settimeout(0.5)  # Set a short timeout for receiving data
        while True:
            try:
                garbage = tcp_socket.recv(1024)  # Attempt to receive data from the socket
                if not garbage:  # If no data is received, break out of the loop
                    break
            except socket.timeout:
                break

    def play_game(self, clients):
        """
        This method generates a trivia question, sends it to each client, receives their answers,
        and determines the game outcome based on the correctness of the answers.
        Args:
            clients (list): A list of tuples containing client sockets and booleans indicating if the clients are active.
        Returns:
            bool: A boolean indicating whether the game should be replayed.
        """
        # Generate a trivia question and its correct answer
        question, oracle_answer = trivia_generator.TriviaGenerator().get_question()
        trivia_question = f'True or false: {question}?\n'
        print(Style.HEADER + f'{trivia_question}' + Style.END_STYLE)
        mutex = threading.Lock()  # Create a mutex for thread safety
        # Iterate over each client and handle sending questions and receiving answers
        for client, player_name in zip(clients, self.player_names):
            if not client[1]:
                # print(Style.WARNING + f'play_game-Inactive Client: {player_name}' + Style.END_STYLE)
                continue
            try:
                # Send the trivia question to the client
                th_send_q = threading.Thread(target=self.send_question, args=(client, player_name, trivia_question))
                th_send_q.start()
                th_send_q.join()
                self.flush_garbage(client, player_name)  # Flush any remaining data in the socket buffer
                client[0].settimeout(10)  # Set a timeout for receiving the answer
                # Receive the answer from the client
                th_get_ans = threading.Thread(target=self.get_answer, args=(client, player_name, mutex, oracle_answer))
                th_get_ans.start()
            except Exception as e:
                print(Style.FAIL + f"Error starting thread: {e}" + Style.END_STYLE)
                return False
        # Wait for answers or timeout
        init_time = datetime.now()
        timeout_duration = 10
        print("Time remaining:")
        while datetime.now() - init_time < timedelta(seconds=timeout_duration) and self.final_answer == [-1, '']:
            self.remaining_time = timeout_duration - (datetime.now() - init_time).seconds
            print(self.remaining_time)
            sleep(1)
        # Determine game status and notify clients
        game_status_msg = 'Expired'
        replay = True
        if self.final_answer[0] == oracle_answer:
            winner = self.final_answer[1]
            game_status_msg = f"\n{winner} is correct! {winner} wins the game!\nCongratulations to the winner: {winner}\n"
            print(Style.BLUE + Style.BOLD + game_status_msg + Style.END_STYLE)
            replay = False
        # Send game status message to each client
        for client, player_name in zip(clients, self.player_names):
            try:
                th_send_game_s = threading.Thread(target=self.send_game_status,
                                                  args=(client, player_name, game_status_msg))
                th_send_game_s.start()
                th_send_game_s.join()
            except Exception as e:
                print(Style.FAIL + f"Error starting thread: {e}" + Style.END_STYLE)
                return False
        return replay

    def get_answer(self, client, player_name, mutex, correct_ans):
        """
        This method receives the answer from a client, processes it, and updates the final answer if it's correct.
        It also handles invalid answers and socket errors.
        Args:
            client (tuple): A tuple containing the client socket and a boolean indicating if the client is active.
            player_name (str): The name of the player associated with the client socket.
            mutex (_thread.lock): A mutex for thread safety.
            correct_ans (int): The correct answer to the trivia question.
        """
        if not client[1]:
            # print(Style.WARNING + f'get_answer-Inactive Client: {player_name}' + Style.END_STYLE)
            return
        client_socket = client[0]
        raw_client_answer = b''  # Initialize raw_client_answer before the try block
        processed_answer = -2
        try:
            raw_client_answer = client_socket.recv(1024).decode().strip()  # Receive and decode the answer
            if not raw_client_answer:
                # print("empty msg")  # debug tool
                client_socket.settimeout(0.01)
                return
            print(Style.CYAN + f'Player: {player_name}, Answer: {raw_client_answer}' + Style.END_STYLE)
            mutex.acquire()  # Acquire mutex to ensure thread safety
            if raw_client_answer.lower() in ['1', 't', 'y']:
                processed_answer = 1  # Treat as True
            elif raw_client_answer.lower() in ['0', 'f', 'n']:
                processed_answer = 0  # Treat as False
            else:
                raise ValueError("Invalid answer format")
        except ValueError as ve:
            print(
                Style.FAIL + f'Player: {player_name} provided an invalid answer: {raw_client_answer}' + Style.END_STYLE)
        except TimeoutError as te:
            # print(Style.FAIL + f'Timeout error for Player: {player_name}. Error: {te}' + Style.END_STYLE)  # debug tool
            return
        except socket.error as se:
            print(Style.FAIL + f"Socket error: {se}" + Style.END_STYLE)
            return

        if processed_answer == correct_ans and self.final_answer[0] != correct_ans:
            self.final_answer[0] = processed_answer
            self.final_answer[1] = player_name
        mutex.release()  # Release mutex after processing answer
        while self.remaining_time > 1 and (not self.final_answer[0] == processed_answer):
            # print(f'self.remaining_time = {self.remaining_time}')
            try:
                client_shit = client_socket.recv(1024).decode().strip()  # Receive additional input from client
                if not client_shit:
                    # print("empty msg") #debug tool
                    client_socket.settimeout(0.01)
                    return
            except socket.timeout as st:
                # Handle socket timeout
                # print(Style.FAIL + f'Socket timeout: {st}' + Style.END_STYLE)
                self.flush_garbage(client, player_name)
                client_socket.settimeout(0.01)
                return
            except socket.error as se:
                print(Style.FAIL + f"Socket error: {se}" + Style.END_STYLE)
                client_socket.settimeout(0.01)
                return
            # print(Style.GRAY + f'{player_name}: {client_shit}' + Style.END_STYLE)
        self.flush_garbage(client, player_name)
        client_socket.settimeout(0.01)  # Set timeout for socket
        return

    def run_server(self):
        """
        This method starts the server, manages client connections, and handles gameplay. It continuously runs the server,
        managing client connections and gameplay until interrupted.
        Note:
            This method continuously runs the server, managing client connections and gameplay until interrupted.
        """
        print(Style.HEADER + Style.BOLD + self.server_name + Style.END_STYLE)
        print(Style.CYAN + f'Server started successfully!' + Style.END_STYLE)
        while True:
            # Start threads for sending UDP offers and accepting TCP client connections
            t1 = threading.Thread(target=self.send_udp_offers)
            t2 = threading.Thread(target=self.tcp_client_connect)
            t1.start()
            t2.start()

            # Wait for threads to finish
            t1.join()
            t2.join()
            welcome_message = self.build_welcome_message()
            for client, player_name in zip(self.clients, self.player_names):
                try:
                    th_send_welcome = threading.Thread(target=self.send_welcome_message, args=(client, welcome_message, player_name))
                    th_send_welcome.start()
                    th_send_welcome.join()
                except Exception as e:
                    print(Style.FAIL + f"send_welcome: Error starting thread: {e}" + Style.END_STYLE)
                    continue

            # Play the game with connected clients
            replay = True
            while replay and self.player_count >= 1:
                replay = self.play_game(self.clients)
                self.remaining_time = 0
                sleep(2)
            # Reset game-related variables
            self.final_answer = [-1, '']
            self.player_names = []
            self.player_count = 0
            self.clients = []

            # Delay before starting the next round
            sleep(1)


if __name__ == '__main__':
    colorama.init()  # Initialize colorama for colored output (if used)
    # Initialize the server with specified parameters
    server = Server(magic_cookie=0xabcddcba, message_type=0x02, server_port=4567, client_port=13117)
    # Run the server
    server.run_server()
