import json
import socket
import base64
import threading
import signal
import sys
import uuid
from utils import load_config
from models import insertMessage  # Import the insertMessage function


def process_message(message, sendingfacility, receivingfacility):

    # Encode content to Base64
    encoded_message = base64.b64encode(message.encode()).decode()

    # generate a GUID
    guid = str(uuid.uuid4())

    # Create a JSON object with the parameters
    content = json.dumps({
        'id': guid,
        'content': encoded_message,
        'sending_facility': sendingfacility,
        'receiving_facility': receivingfacility
    })
       
    # Insert message into the database with PENDING status
    insertMessage(guid, sendingfacility, receivingfacility, content, 'PENDING')
    print(f"Message inserted from {sendingfacility}!")

def handle_client(connection, address, sendingfacility, receivingfacility):
    buffer = ""
    with connection:
        print(f"Client connected from {address}")
        while True:
            data = connection.recv(4096).decode()
            if not data:
                break

            # Append the incoming data to the buffer
            buffer += data

            # Access message type directly from the global config
            message_type = config.get('MessageType', 'generic')

            if message_type == "HL7":
                # Check if we have a complete message (framed by \x0b and \x1c\r)
                while '\x0b' in buffer and '\x1c\r' in buffer:
                    # Find the start and end framing characters
                    start_idx = buffer.find('\x0b')  # Include \x0b in the message
                    end_idx = buffer.find('\x1c\r') + 2  # Include \x1c\r in the message

                    # Extract the complete message including the framing characters
                    complete_message = buffer[start_idx:end_idx]

                    # Process the complete message
                    process_message(complete_message, sendingfacility, receivingfacility)

                    # Send ACK back after processing the complete message
                    connection.sendall(complete_message.encode())

                    # Remove the processed message from the buffer
                    buffer = buffer[end_idx:]  # Keep any remaining data in the buffer
            else:
                # Generic message processing
                process_message(buffer, sendingfacility, receivingfacility)

                # Send ACK for the entire buffer
                connection.sendall(buffer.encode())

                # Clear the buffer after processing
                buffer = ""

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