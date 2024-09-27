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
    message = dequeueMessage([Status.PENDING, Status.RETRY])
    if not message:
        print("No message in the queue.")
        return
    
    # Check status of the dequeued message
    status = Status[message["status"]]

    if status in [Status.PENDING, Status.RETRY]:
        # Send the message to the target postContent REST endpoint
        post_message(message, config)
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