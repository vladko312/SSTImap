 #!/usr/bin/env python

"""
Copyright (c) 2006-2022 sqlmap developers (https://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re
import urllib
import html
import requests

#from bs4 import BeautifulSoup
from mechanize._form import parse_forms
from html5lib import parse

from utils import cliparser
from utils.loggers import log


def crawl(target, args):
    CRAWL_EXCLUDE_EXTENSIONS = ("3ds", "3g2", "3gp", "7z", "DS_Store", "a", "aac", "adp", "ai", "aif", "aiff", "apk", "ar", "asf", "au", "avi", "bak", "bin", "bk", "bmp", "btif", "bz2", "cab", "caf", "cgm", "cmx", "cpio", "cr2", "dat", "deb", "djvu", "dll", "dmg", "dmp", "dng", "doc", "docx", "dot", "dotx", "dra", "dsk", "dts", "dtshd", "dvb", "dwg", "dxf", "ear", "ecelp4800", "ecelp7470", "ecelp9600", "egg", "eol", "eot", "epub", "exe", "f4v", "fbs", "fh", "fla", "flac", "fli", "flv", "fpx", "fst", "fvt", "g3", "gif", "gz", "h261", "h263", "h264", "ico", "ief", "image", "img", "ipa", "iso", "jar", "jpeg", "jpg", "jpgv", "jpm", "jxr", "ktx", "lvp", "lz", "lzma", "lzo", "m3u", "m4a", "m4v", "mar", "mdi", "mid", "mj2", "mka", "mkv", "mmr", "mng", "mov", "movie", "mp3", "mp4", "mp4a", "mpeg", "mpg", "mpga", "mxu", "nef", "npx", "o", "oga", "ogg", "ogv", "otf", "pbm", "pcx", "pdf", "pea", "pgm", "pic", "png", "pnm", "ppm", "pps", "ppt", "pptx", "ps", "psd", "pya", "pyc", "pyo", "pyv", "qt", "rar", "ras", "raw", "rgb", "rip", "rlc", "rz", "s3m", "s7z", "scm", "scpt", "sgi", "shar", "sil", "smv", "so", "sub", "swf", "tar", "tbz2", "tga", "tgz", "tif", "tiff", "tlz", "ts", "ttf", "uvh", "uvi", "uvm", "uvp", "uvs", "uvu", "viv", "vob", "war", "wav", "wax", "wbmp", "wdp", "weba", "webm", "webp", "whl", "wm", "wma", "wmv", "wmx", "woff", "woff2", "wvx", "xbm", "xif", "xls", "xlsx", "xlt", "xm", "xpi", "xpm", "xwd", "xz", "z", "zip", "zipx")
    def crawlThread(curr_depth, current):
        if current in visited:
            return
        elif args.get('crawlExclude') and re.search(args.get('crawlExclude'), current):
            dbgMsg = "skipping '%s'" % current
            log.log(26, dbgMsg)
            return
        else:
            visited.add(current)
        
        content = None
        if current:
            try:
                content = requests.request(method='GET', url=current, proxies={'http': args.get('proxy'), 'https': args.get('proxy')}, verify=args.get('verify_ssl')).text
            except requests.exceptions.ConnectionError as e:
                if e and e.args[0] and e.args[0].args[0] == 'Connection aborted.':
                    log.log(25, 'Error: connection aborted, bad status line.')
                    return
                elif e and e.args[0] and 'Max retries exceeded' in e.args[0].args[0]:
                    log.log(25, 'Error: max retries exceeded for a connection.')
                    return
                else:
                    raise
            
        
        if content:
            try:
                match = re.search(r"(?si)<html[^>]*>(.+)</html>", content)
                if match:
                    content = "<html>%s</html>" % match.group(1)
        
                #soup = BeautifulSoup(content)
                #tags = soup('a')
                tags = []
        
                tags += re.finditer(r'(?i)\s(href|src)=["\'](?P<href>[^>"\']+)', content)
                tags += re.finditer(r'(?i)window\.open\(["\'](?P<href>[^)"\']+)["\']', content)
                
                for tag in tags:
                    href = tag.get("href") if hasattr(tag, "get") else tag.group("href")
                    if href:
                        url = urllib.parse.urljoin(current, html.unescape(href))
                        try:
                            if re.search(r"\A[^?]+\.(?P<result>\w+)(\?|\Z)", url).group("result").lower() in CRAWL_EXCLUDE_EXTENSIONS:
                                continue
                        except AttributeError:      # for extensionless urls
                            pass 
                        if url:
                            worker[curr_depth+1].add(url)
            except UnicodeEncodeError:  # for non-HTML files
                pass
            except ValueError:          # for non-valid links
                pass
            except AssertionError:      # for invalid HTML
                pass
    """"""
    if not target:
        return set()

    visited = set()
    worker = [set([target])]
    results = set()

    try:
        for depth in range(args.get('crawlDepth')): 
            results.update(worker[depth])
            worker.append(set())
            for url in worker[depth]:
                crawlThread(depth, url)
        results.update(worker[args.get('crawlDepth')])
                

        if not results:
            warnMsg = "no usable links found (with GET parameters)"
            log.log(23, warnMsg)

            
        return results
                
        
    except KeyboardInterrupt:
        warnMsg = "user aborted during crawling. "
        warnMsg += "SSTImap will use partial list"
        log.log(26, warnMsg)



def findPageForms(url, args):
    try:
        request = requests.request(method='GET', url=url, proxies={'http': args.get('proxy'), 'https': args.get('proxy')}, verify=args.get('verify_ssl'))
        raw = request.content
        content = request.text
    except requests.exceptions.ConnectionError as e:
        if e and e.args[0] and e.args[0].args[0] == 'Connection aborted.':
            log.log(25, 'Error: connection aborted, bad status line.')
            return set()
        elif e and e.args[0] and 'Max retries exceeded' in e.args[0].args[0]:
            log.log(25, 'Error: max retries exceeded for a connection.')
            return set()
        else:
            raise
    
    forms = None
    if raw:
        try:
            parsed = parse(raw, **{'namespaceHTMLElements': False})
            forms, global_form = parse_forms(parsed, request.url)
        except:
            raise       # TODO: find out what error types these two functions might raise

    retVal = set()
    for form in forms or []:
        try:
            request = form.click()
            if request.type == 'http' or request.type == 'https':
                url = urllib.parse.unquote_plus(request.get_full_url())
                method = request.get_method()
                data = request.data
                
                if data:
                    data = urllib.parse.unquote(request.data)
                    data = data.lstrip("&=").rstrip('&')
                elif not data and method and method.upper() == "POST":
                    debugMsg = "invalid POST form with blank data detected"
                    log.log(26, debugMsg)
                    continue
                    
                target = (url, method, data)
                retVal.add(target)
        except (ValueError, TypeError) as ex:
            errMsg = "there has been a problem while "
            errMsg += "processing page forms ('%s')" % ex
            log.log(26, errMsg)


    try:
        for match in re.finditer(r"\.post\(['\"]([^'\"]*)['\"],\s*\{([^}]*)\}", content):
            url = urllib.parse.urljoin(url, html.unescape(match.group(1)))
            data = ""
    
            for name, value in re.findall(r"['\"]?(\w+)['\"]?\s*:\s*(['\"][^'\"]+)?", match.group(2)):
                data += "%s=%s%s" % (name, value, '&')
    
            data = data.rstrip('&')
            
            target = (url, "POST", data)
            retVal.add(target)
        for match in re.finditer(r"(?s)(\w+)\.open\(['\"]POST['\"],\s*['\"]([^'\"]+)['\"]\).*?\1\.send\(([^)]+)\)", content):
            url = urllib.parse.urljoin(url, html.unescape(match.group(2)))
            data = match.group(3)

            data = re.sub(r"\s*\+\s*[^\s'\"]+|[^\s'\"]+\s*\+\s*", "", data)
            data = data.strip("['\"]")
            
            target = (url, "POST", data)
            retVal.add(target)
    except UnicodeDecodeError:
        pass

    return retVal


