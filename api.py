import json
from flask import Flask, request, jsonify
from models import insertMessage, getUnprocessedMessages, updateMessage
from utils import load_config

app = Flask(__name__)

config = load_config()
# Configuration for the number of messages to fetch
NUM_OF_MESSAGES = config['RESTService']['Methods']['GetContents']['Number']  # number of messages from config file

@app.route('/getcontents', methods=['GET'])
def get_contents():
    messages = getUnprocessedMessages(NUM_OF_MESSAGES)

    contents = []
    # Mark fetched messages as DELIVERED
    for message in messages:
        updateMessage(message['id'], {'status': 'DELIVERED'})  # Update the status in the DB
        contents.append(message['content'])

    return jsonify({"contents": contents, "size": len(contents)}), 200

@app.route('/postcontents', methods=['POST'])
def post_contents():
    data = request.json

    # Check if the 'contents' key exists and is a list
    messages = data.get('contents')

    # Optional: Validate 'size' key
    size = data.get('size')
    if size is not None and not isinstance(size, int):
        return jsonify({"status": "Fail", "error": "'size' must be an integer"}), 400

    for item in messages:
        guid = item.get('id')
        sending_facility = item.get('sending_facility')
        receiving_facility = item.get('receiving_facility')
        content = str(item)

        # Validate individual message payload
        if not all([guid, sending_facility, receiving_facility, content]):
            return jsonify({"status": "Fail", "error": "Missing parameters in one of the messages"}), 400
        
        # Insert each message with status "RECEIVED"
        insertMessage(guid, sending_facility, receiving_facility, content, status="RECEIVED")

    return jsonify({"status": "Success"}), 201


app.run(host='0.0.0.0', port=5000)

