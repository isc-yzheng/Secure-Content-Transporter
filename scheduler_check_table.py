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
def check_queued_message():
    config = load_config()
    if not config:
        print("Configuration error, skipping task...")
        return
    
    # Getting JSON content from the message queue
    message = dequeueMessage()
    if not message:
        print("No message in the queue.")
        return
    
    # Check status of the dequeued message
    status = Status[message["status"]]

    if status in [Status.PENDING, Status.RETRY]:
        # Send the message to the target postContent REST endpoint
        post_message(message, config)
    elif status == Status.RECEIVED:
        # Send the message back to IRIS via TCP
        print("Sending message back to IRIS")
        send_to_TCP(message, config)
    else:
        print(f"Unhandled message status: {status}")

# Send the content from message to the target REST API using the postContent method
def post_message(message, config):
    # Construct the URL from the config
    url = construct_url(config, "PostContent")
    if not url:
        print("URL construction failed, skipping task...")
        return
    
    # Extract content from the dequeue message dict (it's expected to be a JSON string)
    json_string = message["content"]
    
    headers = {
        'Content-Type': 'application/json' # Specify content type as JSON
    }

    try:
        # Send HTTP POST request with raw JSON string
        response = requests.post(url, data=json_string, headers=headers)

        # Parse the JSON response
        response_data = response.json()

        # If the request was succesful, set the message status to "DELIVERED"
        if response_data.get("status") == "Success":
            print(f"{response.status_code}: Message delivered successfully!")
            # Update the message status to 'DELIVERED' in the database
            updateMessage(message['id'], {'status': Status.DELIVERED.name, 'delivered_at': datetime.now()})
        # If the request failed, set the message status to "RETRY"
        else:
            print(f"{response.status_code}: Failed to send message!")
            # Update the message status to 'RETRY' in the database
            updateMessage(message['id'], {'status': Status.RETRY.name})

        print(response_data) #debug

    except Exception as error:
        print("An error occurred:", error)
        # Update the message status to 'RETRY' in the database
        updateMessage(message['id'], {'status': Status.RETRY.name})

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
    scheduler.enter(5, 1, check_queued_message, ())
    # Reschedule the repeat_task
    scheduler.enter(5, 1, repeat_task, ())

# Schedule the first task to run
repeat_task()

# Start the scheduler
print("Scheduler started...\n")
scheduler.run()