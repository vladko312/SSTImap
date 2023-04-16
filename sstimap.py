#!/usr/bin/env python3
import sys
if sys.version_info.major != 3 or sys.version_info.minor < 6:
    print('\033[91m[!]\033[0m SSTImap was created for Python3.6 and above. Python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor)+' is not supported!')
    sys.exit()
import urllib
import importlib
import os
from utils import cliparser
from core import checks
from core.channel import Channel
from core.interactive import InteractiveShell
from utils.loggers import log
from utils.crawler import crawl, find_page_forms
import traceback


version = '1.1.0'


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
    elif args['crawl_depth'] or args['forms']:
        # crawler mode
        urls = set([args.get('url')])
        if args['crawl_depth']:
            crawled_urls = set()
            for url in urls:
                crawled_urls.update(crawl(url, args))
            urls.update(crawled_urls)
        if not args['forms']:
            for url in urls:
                print()
                log.log(23, f'Scanning url: {url}')
                args['url'] = url
                channel = Channel(args)
                checks.check_template_injection(channel)
                if channel.data.get('engine'):
                    break  # TODO: save vulnerabilities
        else:
            forms = set()
            for url in urls:
                forms.update(find_page_forms(url, args))
            for form in forms:
                print()
                log.log(23, f'Scanning form with url: {form[0]}')
                args['url'] = form[0]
                args['method'] = form[1]
                args['data'] = urllib.parse.parse_qs(form[2], keep_blank_values=True)
                channel = Channel(args)
                checks.check_template_injection(channel)
                if channel.data.get('engine'):
                    break  # TODO: save vulnerabilities
                if not forms:
                    log.log(22, f'No forms were detected to scan')
    else:
        # predetermined mode
        checks.check_template_injection(Channel(args))


def load_plugins():
    importlib.invalidate_caches()
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
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        log.log(22, 'Exiting')
    except Exception as e:
        log.critical('Error: {}'.format(e))
        log.debug(traceback.format_exc())
        raise e
