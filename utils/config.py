import os
import json

config = {}

config_folder = os.path.dirname(os.path.realpath(__file__))

# TODO: fix this
with open(config_folder + "/../config.json", 'r') as stream:
    try:
        config = json.load(stream)
    except json.JSONDecodeError as e:
        print(f'[!][config] {e}')

base_path = os.path.expanduser(config.get("base_path", "~/.sstimap/"))
log_response = config.get("log_response", False)
time_based_blind_delay = config.get("time_based_blind_delay", 4)

if not os.path.isdir(base_path):
    os.makedirs(base_path)


