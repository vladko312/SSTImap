#!/usr/bin/env python3
import sys
from utils import cliparser
from core import checks
from core.channel import Channel
from core.interactive import InteractiveShell
from utils.loggers import log
import traceback

version = '1.0.1'


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


if __name__ == '__main__':
    print(cliparser.banner())
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
