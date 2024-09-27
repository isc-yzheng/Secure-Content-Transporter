import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import insertMessage, getUnprocessedMessages, updateMessage

app = Flask(__name__)

# Configure the existing SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sct.db'  # Adjust the path as needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

    if not isinstance(data, list):
        return jsonify({"status": "Fail", "error": "Payload must be an array of messages"}), 400

    for item in data:
        sending_facility = item.get('sending_facility')
        receiving_facility = item.get('receiving_facility')
        content = item.get('content')

        # Validate individual message payload
        if not all([sending_facility, receiving_facility, content]):
            return jsonify({"status": "Fail", "error": "Missing parameters in one of the messages"}), 400
        
        # Insert each message with status "RECEIVED"
        insertMessage(sending_facility, receiving_facility, content, status="RECEIVED")

    return jsonify({"status": "Success"}), 201

@app.route('/postcontent', methods=['POST'])
def post_content():
    data = request.json
    sending_facility = data.get('sending_facility')
    receiving_facility = data.get('receiving_facility')
    content = data.get('content')

    # Validate input
    if not all([sending_facility, receiving_facility, content]):
        return jsonify({"status": "Fail", "error": "Missing parameters"}), 400

    # Insert message using the function from your module
    insertMessage(sending_facility, receiving_facility, content, status="PENDING")

    return jsonify({"status": "Success"}), 201


app.run(port=5000)
