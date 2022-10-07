#!/usr/bin/env python3
import importlib
import os
import sys
from utils import cliparser
from core import checks
from core.channel import Channel
from core.interactive import InteractiveShell
from utils.loggers import log
import traceback

version = '1.0.2'


def main():
    args = vars(cliparser.options)
    args['version'] = version
    if not (args['url'] or args['interactive']):
        # no target specified
        log.log(22, 'SSTImap requires target url (-u, --url) or interactive mode (-i, --interactive)')
    elif args['interactive']:
        # interactive mode
        log.log(23, 'Starting SSTImap in interactive mode. Type \'help\' to see the details.')
        InteractiveShell(args).cmdloop()
    else:
        # predetermined mode
        checks.check_template_injection(Channel(args))


def load_plugins():
    groups = os.scandir("plugins")
    groups = filter(lambda x: x.is_dir(), groups)
    for g in groups:
        modules = os.scandir(f"plugins/{g.name}")
        modules = filter(lambda x: (x.name.endswith(".py") and not x.name.startswith("_")), modules)
        for m in modules:
            importlib.import_module(f"plugins.{g.name}.{m.name[:-3]}")


if __name__ == '__main__':
    print(cliparser.banner())
    load_plugins()
    from core.plugin import loaded_plugins
    log.log(26, f"Loaded plugins by categories: {'; '.join([f'{x}: {len(loaded_plugins[x])}' for x in loaded_plugins])}\n")
    if sys.version_info.major != 3:
        log.critical(f'SSTImap was created for Python3. Python{sys.version_info.major} is not supported!')
        sys.exit()
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        log.log(22, 'Exiting')
    except Exception as e:
        log.critical('Error: {}'.format(e))
        log.debug(traceback.format_exc())
        raise e
