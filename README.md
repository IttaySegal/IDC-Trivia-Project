# IDC Trivia Project

This project is a **Trivia Game** designed for the IDC course at Ben-Gurion University. It establishes a TCP connection between a server and multiple clients, facilitating a multiplayer trivia game with timed responses.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [File Descriptions](#file-descriptions)
- [License](#license)

## Project Overview

The goal of this project is to enable a trivia game where a server sends questions to clients over a TCP connection. Each client has 10 seconds to answer. If a client answers incorrectly or fails to respond in time, the next question is sent until one client wins. Upon winning, the server restarts and looks for new client connections, allowing continuous play.

## Features

- **Multiplayer Support**: Connects multiple clients to a single server for group trivia play.
- **Timed Responses**: Each client has a 10-second window to answer each question.
- **Automatic Restart**: Server resets to allow new players to join after a game ends.
- **Trivia Pool**: Over 30 unique trivia questions with true/false answers.

## Installation and Setup

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/shvants/IDC-Trivia-Project.git
    cd IDC-Trivia-Project
    ```

2. **Dependencies**:
    - Ensure you have Python installed (preferably Python 3.6+).
    - Install the necessary libraries:
      ```bash
      pip install colorama scapy
      ```

3. **Running the Server**:
   - In one terminal window, start the server:
     ```bash
     python server.py
     ```

4. **Running the Client**:
   - In separate terminal windows, start each client instance:
     ```bash
     python client.py
     ```

## Usage

- Start the server, which will broadcast a UDP message to identify clients.
- Each client listens for the server’s broadcast and connects to it.
- Once connected, the server sends trivia questions, and each client answers.
- If a client wins by correctly answering a question, the game ends, and the server resets.

## File Descriptions

- **`client.py`**: Contains the `Client` class, responsible for connecting to the server, receiving trivia questions, and sending answers.
- **`server.py`**: Contains the `Server` class, which handles broadcasting, accepting client connections, and managing game rounds.
- **`style.py`**: Defines text styles (colors and formats) for terminal output, enhancing user experience.
- **`trivia_generator.py`**: Defines the `TriviaGenerator` class, managing the trivia question pool and ensuring each question is unique per session.
- **`README.md`**: Documentation for project setup, usage, and features.

## License

This project is licensed under the MIT License.
