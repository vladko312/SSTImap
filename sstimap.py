#!/usr/bin/env python3
import sys
from pathlib import Path
if sys.version_info.major != 3 or sys.version_info.minor < 6:
    print('\033[91m[!]\033[0m SSTImap was created for Python3.6 and above. Python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor)+' is not supported!')
    sys.exit()
if sys.version_info.minor > 13:
    print('\033[33m[!]\033[0m This version of SSTImap was not tested with Python3.'+str(sys.version_info.minor))
import importlib
import os
from utils import cliparser
from core import checks
from core.interactive import InteractiveShell
from utils.loggers import log
from utils.config import config_args, version
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent
PLUGINS_DIR = PROJECT_ROOT / "plugins"
DATA_TYPES_DIR = PROJECT_ROOT / "data_types"

def main():
    args = vars(cliparser.options)
    args = config_args(args)
    args['version'] = version
    from utils.loggers import formatter, no_colour
    formatter.colour = args.get("colour", True)
    if formatter.colour:
        print(cliparser.banner())
    else:
        print(no_colour(cliparser.banner()))
    load_plugins()
    from core.plugin import loaded_plugins
    log.log(26, f"Loaded plugins by categories: {'; '.join([f'{x}: {len(loaded_plugins[x])}' for x in loaded_plugins])}")
    load_data_types()
    from core.data_type import loaded_data_types
    log.log(26, f"Loaded request body types: {len(loaded_data_types)}\n")
    if not (args['url'] or args['interactive'] or args['load_urls'] or args['load_forms'] or args['module']):
        # no target specified
        log.log(22, 'SSTImap requires target URL (-u, --url), URLs/forms file (--load-urls / --load-forms) '
                    'or interactive mode (-i, --interactive)')
    elif args['module']:
        # module list / help
        checks.module_info("" if args['module'] == 'list' else args['module'])
    elif args['interactive']:
        # interactive mode
        log.log(23, "Starting SSTImap in interactive mode. Type 'help' to see the details.")
        InteractiveShell(args).cmdloop()
    else:
        # predetermined mode
        checks.scan_website(args)


def load_plugins():
    importlib.invalidate_caches()
    if not PLUGINS_DIR.is_dir():
        return
    for g in PLUGINS_DIR.iterdir():
        if not g.is_dir():
            continue
        for m in g.iterdir():
            if m.name.endswith(".py") and not m.name.startswith("_"):
                importlib.import_module(f"plugins.{g.name}.{m.stem}")


def load_data_types():
    importlib.invalidate_caches()
    if not DATA_TYPES_DIR.is_dir():
        return
    for m in DATA_TYPES_DIR.iterdir():
        if m.name.endswith(".py") and not m.name.startswith("_"):
            importlib.import_module(f"data_types.{m.stem}")

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        log.log(22, 'Exiting')
    except Exception as e:
        log.critical('Error: {}'.format(e))
        log.debug(traceback.format_exc())
        raise e
