import json
import socket
import requests
import sqlite3
from datetime import datetime

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


    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to a specific address and port
    server_socket.bind(('', listen_port))
    
    # Listen for incoming connections
    server_socket.listen(1)
    print(f"Listening on port {listen_port}")

    while True:
        # Wait for a connection
        client_socket, address = server_socket.accept()
        print(f"Got connection from {address}")

        try:
            # Receive data from the client
            data = client_socket.recv(1024).decode('utf-8')
            print(f"Received: {data}")

            # Send data to the specified endpoint
            response = requests.post(endpoint_url, data=data)
            print(f"Sent to endpoint. Response: {response.status_code}")

            # Send acknowledgment back to the client
            client_socket.send("Data received and forwarded".encode('utf-8'))

        except Exception as e:
            print(f"Error: {e}")

        finally:
            # Close the connection
            client_socket.close()
        
    # Close the database connection
    conn.close()

# Read the config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Extract the ports to listen on
listen_ports = [item['Port'] for item in config['ListenTo']]

# This section needs further development
for port in listen_ports:
    # code to set up listening on each port
    break
    
db_path = "sct.db" 

endpoint_url = "https://postman-echo.com/post"  # URL to send data to

listen_and_send(port, endpoint_url)