import json

# Load configuration from config.json
def load_config():
    config = None
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print("Config file not found!")
    except json.JSONDecodeError:
        print("Error decoding the config file!")
    finally:
        return config
    
# Function to construct the URL from the config JSON object
def construct_url(config, method):
    try:
        protocol = config["RESTDestination"]["Protocol"]
        hostname = config["RESTDestination"]["Hostname"]
        port = config["RESTDestination"]["Port"]
        basepath = config["RESTDestination"]["BasePath"]
        path = config["RESTDestination"]["Methods"][method]["Path"]

        # Construct the URL (include port if it's provided)
        if port:
            url = f"{protocol}://{hostname}:{port}{basepath}{path}"
        else:
            url = f"{protocol}://{hostname}{basepath}{path}"
    except KeyError:
        print("Missing configuration key in config.json!")
        url = None
    finally:
        return url