import sched
import time
from utils import load_config, construct_url
import requests
from models import insertMessage, Status

# Create a scheduler instance
scheduler = sched.scheduler(time.time, time.sleep)

# Define the task to run
def pull_messages():
    print("Pulling Messages...")

    # Load configuration
    config = load_config()
    if not config:
        print("Configuration error, skipping task...")
        return
    
    # Construct the URL for the GET request for GetContents endpoint
    url = construct_url(config, "GetContents")
    if not url:
        print("URL construction failed, skipping task...")
        return

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Send the GET request
        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            messages = response_data.get("messages", [])
            for message in messages:
                sending_facility = message["sending_facility"]
                receiving_facility = message["receiving_facility"]
                content = message["content"]

                # Insert each message into the message_queue table with status "RECEIVED"
                insertMessage(sending_facility, receiving_facility, content, Status.RECEIVED.name)
            
            print(f"Inserted {len(messages)} messages into the database.")
        else:
            print(f"Failed to pull messages, Status Code: {response.status_code}")

    except Exception as error:
        print(f"An error occurred while pulling messages: {error}")

def repeat_task():
    scheduler.enter(5, 1, pull_messages, ())
    # Reschedule the task again
    scheduler.enter(5, 1, repeat_task, ())

# Schedule the first task to run after 5 minutes
repeat_task()

# Start the scheduler
print("Scheduler started...")
scheduler.run()
