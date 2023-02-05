#!/usr/bin/env python3
import sys
import urllib

from utils import cliparser
from core import checks
from core.channel import Channel
from core.interactive import InteractiveShell
from utils.loggers import log
from utils.crawler import crawl, findPageForms
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
    elif args['crawlDepth'] or args['forms']:
        # crawler mode
        urls = set([args.get('url')])
        if args['crawlDepth']:
            crawled_urls = set()
            for url in urls:
                crawled_urls.update(crawl(url, args))
            urls.update(crawled_urls)
        if not args['forms']:
            for url in urls:
                args['url'] = url
                checks.check_template_injection(Channel(args))
        else:
            forms = set()
            for url in urls:
                forms.update(findPageForms(url, args))
            for form in forms:
                args['url'] = form[0]
                args['method'] = form[1]
                args['data'] = urllib.parse.parse_qs(form[2], keep_blank_values=True)
                checks.check_template_injection(Channel(args))
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
