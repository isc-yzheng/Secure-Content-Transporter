import json
from flask import Flask, request, jsonify
from models import insertMessage, getUnprocessedMessages, updateMessage

app = Flask(__name__)

# Configuration for the number of messages to fetch
NUM_OF_MESSAGES = 5  # Adjust this value based on your config

@app.route('/getcontents', methods=['POST'])
def get_contents():
    messages = getUnprocessedMessages(NUM_OF_MESSAGES)

    # Mark fetched messages as DELIVERED
    for message in messages:
        updateMessage(message['id'], {'status': 'DELIVERED'})  # Update the status in the DB

    return jsonify({"messages": messages, "size": len(messages)}), 200

@app.route('/postcontents', methods=['POST'])
def post_contents():
    data = request.json

    # Check if the 'messages' key exists and is a list
    messages = data.get('messages')

    if not isinstance(data, list):
        return jsonify({"status": "Fail", "error": "Payload must be an array of messages"}), 400

    # Optional: Validate 'size' key
    size = data.get('size')
    if size is not None and not isinstance(size, int):
        return jsonify({"status": "Fail", "error": "'size' must be an integer"}), 400

    for item in messages:
        sending_facility = item.get('sending_facility')
        receiving_facility = item.get('receiving_facility')
        content = item.get('content')

        # Validate individual message payload
        if not all([sending_facility, receiving_facility, content]):
            return jsonify({"status": "Fail", "error": "Missing parameters in one of the messages"}), 400
        
        # Insert each message with status "RECEIVED"
        insertMessage(sending_facility, receiving_facility, content, status="RECEIVED")

    return jsonify({"status": "Success"}), 201


app.run(host='0.0.0.0', port=5000)

