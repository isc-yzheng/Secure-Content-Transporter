import sched
import time
import requests
from utils import load_config, construct_url
from models import updateMessage, dequeueMessages, Status
from datetime import datetime
import json
import sys


# Create a scheduler instance
scheduler = sched.scheduler(time.time, time.sleep)

# Load config.json
config = load_config()
if not config:
    print("Failed to load configuration file, Shuting down the scheduler...")
    sys.exit(0)

SCHEDULER_INTERVAL = config["Schedulers"]["PostMessage"]["interval"]

# Task to run: Dequeue top message in ascending order of created_at with status not "DELIVERED" or "COMPLETED"
def check_queued_message():
    print("Dequeueing and Posting Message...")

    # Getting a snapshot of pending/retry messages from the message queue for processing
    messages = dequeueMessages([Status.PENDING, Status.RETRY], 10)
    if not messages:
        print("No message in the queue.")
        return
    
    for message in messages:
        # Check status of the dequeued message
        status = Status[message["status"]]

        if status in [Status.PENDING, Status.RETRY]:
            # Send the message to the target postContent REST endpoint
            post_message(message)
        else:
            print(f"Unhandled message status: {status}")

# Send the content from message to the target REST API using the postContent method
def post_message(message):
    # Construct the URL from the config
    url = construct_url(config, "PostContents")
    if not url:
        print("URL construction failed, skipping task...")
        return
    
    # Extract content from the dequeue message dict (it's expected to be a JSON string)
    # Extract content and transform it into a Python dict
    try:
        message_content = json.loads(message['content'])
        request_json = {
            "contents": [
                message_content
            ],
            "size": 1
        }
    except json.JSONDecodeError as error:
        print(f"Failed to parse content for message id {message['id']}: {error}")
        return
    
    headers = {
        'Content-Type': 'application/json' # Specify content type as JSON
    }

    try:
        # Send HTTP POST request with raw JSON string
        response = requests.post(url, json=request_json, headers=headers)

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
    scheduler.enter(SCHEDULER_INTERVAL, 1, check_queued_message, ())
    # Reschedule the repeat_task
    scheduler.enter(SCHEDULER_INTERVAL, 1, repeat_task, ())

# Schedule the first task to run
repeat_task()

# Start the scheduler
print(f"Scheduler started, runs every {SCHEDULER_INTERVAL} seconds...\n")
scheduler.run()