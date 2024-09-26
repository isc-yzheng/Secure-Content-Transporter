import sched
import time
from utils import load_config, construct_url
import requests
from models import getUnprocessedMessages, updateMessage, Status
import json

# Create a scheduler instance
scheduler = sched.scheduler(time.time, time.sleep)

# Define the task to run
def push_messages():
    print("Pushing Messages...")

    # Load configuration
    config = load_config()
    if not config:
        print("Configuration error, skipping task...")
        return
    
    # Get the number of messages to fetch from the updated config
    num_of_messages = config.get("RESTService", {}).get("Methods", {}).get("PostContents", {}).get("Number", 1)
    
    # Retrieve unprocessed messages (PENDING or RETRY status)
    messages = getUnprocessedMessages(num_of_messages)

    # If no messages to push, exit the function
    if not messages:
        print("No unprocessed messages to push.")
        return

    # Construct the URL for the PostContents endpoint
    url = construct_url(config, "PostContents")
    if not url:
        print("URL construction failed, skipping task...")
        return

    headers = {
        'Content-Type': 'application/json'  # Specify content type as JSON
    }

    # Prepare the request body, which is a list of "content" fields from each message
    request_body = [json.loads(message['content']) for message in messages]
    
    try:
        # Send HTTP POST request with the list of content fields
        response = requests.post(url, json=request_body, headers=headers)

        # Parse the JSON response
        response_data = response.json()

        # If the request was successful
        if response_data.get("status") == "Success":
            for message in messages:
                # Update each message's status to "DELIVERED"
                updateMessage(message['id'], {"status": Status.DELIVERED.name})
            print(f"Successfully pushed {len(messages)} messages.")
        else:
            print(f"Failed to push messages: {response_data.get('error')}")
            # Optionally update messages to RETRY if failed
            for message in messages:
                updateMessage(message['id'], {"status": Status.RETRY.name})

    except Exception as error:
        print("An error occurred while pushing messages:", error)

def repeat_task():
    scheduler.enter(5, 1, push_messages, ())
    # Reschedule the task again
    scheduler.enter(5, 1, repeat_task, ())

# Schedule the first task to run after 5 minutes
repeat_task()

# Start the scheduler
print("Scheduler started...")
scheduler.run()
