import json
import socket
import requests
import sqlite3
import base64
from datetime import datetime
import threading

from models import insertMessage  # Import the insertMessage function


db_path = "sct.db" 

def process_message(message, sendingfacility, receivingfacility):

    # Create a JSON object with the parameters
    content = json.dumps({
        'message': message,
        'sendingFacility': sendingfacility,
        'receivingFacility': receivingfacility
    })
    # Encode content to Base64
    encoded_content = base64.b64encode(content.encode()).decode()
       
    # Insert message into the database with PENDING status
    insertMessage(sendingfacility, receivingfacility, encoded_content, 'PENDING')

def handle_client(connection, address, sendingfacility, receivingfacility):
    with connection:
        print(f"Client connected from {address}")
        while True:
            data = connection.recv(1024)
            if not data:
                break

            message = data.decode()
            process_message(message, sendingfacility, receivingfacility)
            connection.sendall(data)  # Echo the data back

def listen_on_port(port, sendingfacility, receivingfacility):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('127.0.0.1', port))
        server_socket.listen()
        print(f"Listening on port: {port}.")
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, sendingfacility, receivingfacility))
            client_thread.start()

# Read the config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


# Extract the ports to listen on
ports = [item['Port'] for item in config['ListenTo']]
# Extract sending facility info
sending_facilities = [item['SendingFacility'] for item in config['ListenTo']]
receiving_facilities = [item['ReceivingFacility'] for item in config['ListenTo']]

threads = []
for port, sendingfacility, receivingfacility in zip(ports, sending_facilities, receiving_facilities):  # Use zip to pair ports and facilities
    thread = threading.Thread(target=listen_on_port, args=(port, sendingfacility, receivingfacility))  # Pass both args
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()


endpoint_url = "https://postman-echo.com/post"  # URL to send data to

# listen_and_send(port, endpoint_url)