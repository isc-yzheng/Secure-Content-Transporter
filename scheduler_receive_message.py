import sched
import time
import requests
from utils import load_config, construct_url
from models import updateMessage, dequeueMessage, Status
from datetime import datetime
import socket
import json
import base64


# Create a scheduler instance
scheduler = sched.scheduler(time.time, time.sleep)

# Task to run: Dequeue top message in ascending order of created_at with status not "DELIVERED" or "COMPLETED"
def check_received_message():
    config = load_config()
    if not config:
        print("Configuration error, skipping task...")
        return
    
    # Getting JSON content from the message queue
    message = dequeueMessage([Status.RECEIVED])
    if not message:
        print("No message in the queue.")
        return
    
    # Check status of the dequeued message
    status = Status[message["status"]]

    if status == Status.RECEIVED:
        # Send the message back to IRIS via TCP
        print("Sending message back to IRIS")
        send_to_TCP(message, config)
    else:
        print(f"Unhandled message status: {status}")

# Send message to a socket port via TCP
def send_to_TCP(message, config):
    receiving_facility = message['receiving_facility']
    
    # The message['content'] is expected to be a JSON string, so we parse it into a Python dict
    try:
        content_dict = json.loads(message['content'])
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON content: {e}")
        return

    # Get the actual content from the 'content' field of the parsed JSON
    encoded_content = content_dict.get('content')
    if not encoded_content:
        print(f"Missing 'content' field in the message content: {message['content']}")
        return

    # Decode the BASE64-encoded content
    try:
        decoded_content = base64.b64decode(encoded_content).decode('utf-8')
    except Exception as e:
        print(f"Failed to decode BASE64 content: {e}")
        return

    # Get the port number from the config for the receiving facility
    try:
        port = config['SendBack'].get(receiving_facility)
        if not port:
            print(f"No port found for receiving facility: {receiving_facility}")
            return
    except KeyError:
        print(f"Error accessing port configuration for {receiving_facility}")
        return

    # Send the decoded content to the designated port via TCP
    try:
        # Create a TCP/IP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Connect to the server on the specified port (assuming localhost)
            s.connect(('localhost', port))

            # Send the decoded content via TCP
            s.sendall(decoded_content.encode('utf-8'))

            # Receive and print the response
            response = s.recv(1024).decode('utf-8')
            print(f"Response from TCP server: {response}")

    except Exception as e:
        print(f"An error occurred while sending TCP message: {e}")

def repeat_task():
    # schedule check_queued_message
    scheduler.enter(5, 1, check_received_message, ())
    # Reschedule the repeat_task
    scheduler.enter(5, 1, repeat_task, ())

# Schedule the first task to run
repeat_task()

# Start the scheduler
print("Scheduler started...\n")
scheduler.run()