import json
import socket
import requests
import sqlite3
from datetime import datetime
import threading

db_path = "sct.db" 

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       content TEXT)''')
    conn.commit()

def save_message(conn, timestamp, content):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (timestamp, content) VALUES (?, ?)",
                   (timestamp, content))
    conn.commit()

def listen_and_send(listen_port, endpoint_url):

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    create_table(conn)

def handle_client(connection, address):
    with connection:
        print(f"Client connected from {address}")
        while True:
            data = connection.recv(1024)
            if not data:
                break
            print(f"Received: {data.decode()}")
            connection.sendall(data)  # Echo the data back

def listen_on_port(port, facility):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('127.0.0.1', port))
        server_socket.listen()
        print(f"Listening on port: {port} with facility: {facility}")
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

# Read the config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


# Extract the ports to listen on
ports = [item['Port'] for item in config['ListenTo']]
# Extract sending facility info
sending_facilities = [item['SendingFacility'] for item in config['ListenTo']]

threads = []
for port, facility in zip(ports, sending_facilities):  # Use zip to pair ports and facilities
    thread = threading.Thread(target=listen_on_port, args=(port, facility))  # Pass both args
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()




endpoint_url = "https://postman-echo.com/post"  # URL to send data to

# listen_and_send(port, endpoint_url)