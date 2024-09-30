import json
import socket
import base64
import threading
import signal
import sys
from utils import load_config

from models import insertMessage  # Import the insertMessage function


def process_message(message, sendingfacility, receivingfacility):

    # Encode content to Base64
    encoded_message = base64.b64encode(message.encode()).decode()

    # Create a JSON object with the parameters
    content = json.dumps({
        'content': encoded_message,
        'sending_facility': sendingfacility,
        'receiving_facility': receivingfacility
    })
       
    # Insert message into the database with PENDING status
    insertMessage(sendingfacility, receivingfacility, content, 'PENDING')

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
            client_thread.daemon = True  # Set as daemon so it exits with the main program
            client_thread.start()

# Signal handler for clean shutdown
def signal_handler(sig, frame):
    print(f"Received signal: {sig}")
    print(f"Frame: {frame}")
    print('Shutting down...')
    sys.exit(0)

# Register signal handler for Control + C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)

# Read the config file
config = load_config()

# Extract the ports to listen on
ports = [item['Port'] for item in config['ListenTo']]
# Extract sending facility info
sending_facilities = [item['SendingFacility'] for item in config['ListenTo']]
receiving_facilities = [item['ReceivingFacility'] for item in config['ListenTo']]

threads = []
for port, sendingfacility, receivingfacility in zip(ports, sending_facilities, receiving_facilities):  # Use zip to pair ports and facilities
    thread = threading.Thread(target=listen_on_port, args=(port, sendingfacility, receivingfacility))  # Pass both args
    thread.daemon = True  # Ensure threads exit with main program
    threads.append(thread)
    thread.start()

# for thread in threads:
#     thread.join()

# Keep main thread alive to listen for keyboard interrupt
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Keyboard interrupt received. Exiting...")
    sys.exit(0)