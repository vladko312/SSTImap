import os
import sys
import json


version = '1.2.0'

# Defaults to be overwritten by config.json, ~/.sstimap/config.json, user-supplied config and arguments
defaults = {
    "base_path": "~/.sstimap/",
    "crawl_depth": 0,
    "marker": '*',
    "level": 1,
    "technique": "RT",
    "crawl_domains": "S",
    "log_response": False,
    "time_based_blind_delay": 4,
    "user_agent": f'SSTImap/{version}',
    "interactive": False,
    "random_agent": False,
    "verify_ssl": False,
    "forms": False,
    "legacy": False,
    "tpl_shell": False,
    "eval_shell": False,
    "os_shell": False,
    "force_overwrite": False
}
config = {}
user_config = {}

# TODO: fix this
with open(f"{sys.path[0]}/config.json", 'r') as stream:
    try:
        config = json.load(stream)
    except json.JSONDecodeError as e:
        print(f'[!][config] {repr(e)}')

base_path = os.path.expanduser(config.get("base_path", "~/.sstimap/"))
if not os.path.isdir(base_path):
    os.makedirs(base_path)

if os.path.exists(f"{base_path}/config.json"):
    with open(f"{base_path}/config.json", 'r') as stream:
        try:
            user_config = json.load(stream)
        except json.JSONDecodeError as e:
            print(f'[!][user config] {repr(e)}')


def config_update(base, added):
    for i in added:
        if added[i] is not None or i not in base:
            base[i] = added[i]


def config_args(args):
    res = defaults.copy()
    config_update(res, config)
    config_update(res, user_config)
    custom = args.get("config", res.get("config", None))
    if custom:
        if os.path.isdir(custom):
            custom = f"{custom}/config.json"
        if os.path.exists(custom):
            custom_config = {}
            with open(custom, 'r') as stream:
                try:
                    custom_config = json.load(stream)
                except json.JSONDecodeError as e:
                    print(f'[!][custom config] {repr(e)}')
            config_update(res, custom_config)
    config_update(res, args)
    return res
