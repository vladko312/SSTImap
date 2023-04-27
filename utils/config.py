import os
import sys
import json

defaults = {
    "crawl_depth": 0,
    "marker": '*',
    "level": 1,
    "technique": "RT",
    "crawl_domains": "S",
    "log_response": False,
    "time_based_blind_delay": 4
}
config = {}
user_config = {}

# TODO: fix this
with open(f"{sys.path[0]}/config.json", 'r') as stream:
    try:
        config = json.load(stream)
    except json.JSONDecodeError as e:
        print(f'[!][config] {e}')

base_path = os.path.expanduser(config.get("base_path", "~/.sstimap/"))
if not os.path.isdir(base_path):
    os.makedirs(base_path)

if os.path.exists(f"{base_path}/config.json"):
    with open(f"{base_path}/config.json", 'r') as stream:
        try:
            user_config = json.load(stream)
        except json.JSONDecodeError as e:
            print(f'[!][user config] {e}')


def config_update(base, added):
    for i in added:
        if added[i] is not None or i not in base:
            base[i] = added[i]


def config_args(args):
    res = defaults.copy()
    config_update(res, config)
    config_update(res, user_config)
    config_update(res, args)
    return res
