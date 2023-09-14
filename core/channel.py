import json
import time

import requests
import urllib3
from utils.loggers import log
from urllib import parse
from copy import deepcopy
from utils.random_agent import get_agent


class Channel:
    def __init__(self, args):
        self.args = args
        self.url = self.args.get('url').replace('#', '%23').replace('\\n', '%0A')
        self.base_url = self.url.split("?")[0] if '?' in self.url else self.url
        self.tag = self.args.get('marker')
        self.data = {}
        self.injs = []
        self.inj_idx = 0
        proxy = self.args.get('proxy')
        if proxy:
            self.proxies = {'http': proxy, 'https': proxy}
        else:
            self.proxies = {}
        self.get_params = {}
        self.post_params = {}
        self.header_params = {}
        self.cookie_params = {}
        self._parse_url()
        self._parse_get()
        self._parse_post()
        self._parse_header()
        self._parse_cookies(self.args.get('cookies', []))
        if not self.injs:
            self._parse_get(all_injectable=True)
            self._parse_post(all_injectable=True)
            self._parse_header(all_injectable=True)
            self._parse_cookies(self.args.get('cookies', []), all_injectable=True)
        self._parse_method()
        if not self.args.get('verify_ssl'):
            urllib3.disable_warnings()
        
    def _parse_method(self):
        if self.args.get('method'):
            self.http_method = self.args.get('method')
        elif self.post_params:
            self.http_method = 'POST'
        else:
            self.http_method = 'GET'

    def _parse_url(self):
        url_path = parse.urlparse(self.url).path
        if self.tag not in url_path:
            return
        url_path_base_index = self.url.find(url_path)
        for index in [i for i in range(url_path_base_index, url_path_base_index + len(url_path))
                      if self.url[i] == self.tag]:
            self.injs.append({'field': 'URL', 'param': 'url', 'position': url_path_base_index + index})

    def _parse_cookies(self, cookies, all_injectable=False):
        # Just add cookies as headers, to avoid duplicating
        # the parsing code. Concatenate to avoid headers with
        # the same key.
        if cookies:
            splitted_cookies = []
            for cookie in cookies:
                for param_value in cookie.split(';'):
                    if '=' in param_value:
                        splitted_cookies.append(param_value)
            for cookie in splitted_cookies:
                param, value = cookie.split('=', 1)
                param = param.strip()
                value = value.strip()
                self.cookie_params[param] = value
                if self.tag in param:
                    self.injs.append({'field': 'Cookie', 'part': 'param', 'param': param})
                if self.tag in value or all_injectable:
                    self.injs.append({'field': 'Cookie', 'part': 'value', 'value': value, 'param': param})
            #cookie_string = f"Cookie: {';'.join(cookies)}"
            #if not self.args.get('headers'):
            #    self.args['headers'] = []
            #self.args['headers'].append(cookie_string)

    def _parse_header(self, all_injectable=False):
        headers = []
        for header in self.args.get('headers', []):
            for param_value in header.split('\r\n'):
                if ':' in param_value:
                    headers.append(param_value)
        for param_value in headers:
            param, value = param_value.split(':', 1)
            param = param.strip()
            value = value.strip()
            if param.lower() == "cookie":
                self._parse_cookies([value], all_injectable=all_injectable)
            else:
                self.header_params[param] = value
                if self.tag in param:
                    self.injs.append({'field': 'Header', 'part': 'param', 'param': param})
                if self.tag in value or all_injectable:
                    self.injs.append({'field': 'Header', 'part': 'value', 'value': value, 'param': param})
        if self.args.get('content_type') == "json":
            self.header_params["Content-Type"] = "application/json"

    def _parse_post(self, all_injectable=False):
        if self.args.get('data'):
            if self.args.get('content_type') == "json":
                json_data = json.loads(self.args.get('data')[0])
                for param in json_data:
                    value_list = json_data[param]
                    self.post_params[param] = value_list
                    if self.tag in param:
                        self.injs.append({'field': 'POST', 'part': 'param', 'param': param})
                    for idx, value in enumerate(value_list):
                        if self.tag in value or all_injectable:
                            self.injs.append({'field': 'POST', 'part': 'value', 'value': value, 'param': param, 'idx': idx})
            else:
                params_dict_list = parse.parse_qs('&'.join(self.args.get('data')), keep_blank_values=True)
                for param, value_list in params_dict_list.items():
                    self.post_params[param] = value_list
                    if self.tag in param:
                        self.injs.append({'field': 'POST', 'part': 'param', 'param': param})
                    for idx, value in enumerate(value_list):
                        if self.tag in value or all_injectable:
                            self.injs.append({'field': 'POST', 'part': 'value', 'value': value, 'param': param, 'idx': idx})

    def _parse_get(self, all_injectable=False):
        params_dict_list = parse.parse_qs(parse.urlsplit(self.url).query, keep_blank_values=True)
        for param, value_list in params_dict_list.items():
            self.get_params[param] = value_list
            if self.tag in param:
                self.injs.append({'field': 'GET', 'part': 'param', 'param': param})
            for idx, value in enumerate(value_list):
                if self.tag in value or all_injectable:
                    self.injs.append({'field': 'GET', 'part': 'value', 'param': param, 'value': value, 'idx': idx})
            
    def req(self, injection):
        get_params = deepcopy(self.get_params)
        post_params = deepcopy(self.post_params)
        header_params = deepcopy(self.header_params)
        cookie_params = deepcopy(self.cookie_params)
        url_params = self.base_url
        inj = deepcopy(self.injs[self.inj_idx])
        if inj['field'] == 'URL':
            position = inj['position']
            url_params = self.base_url[:position] + injection + self.base_url[position+1:]
        elif inj['field'] == 'POST':
            if inj.get('part') == 'param':
                old_value = post_params[inj.get('param')]
                del post_params[inj.get('param')]
                if self.tag in inj.get('param'):
                    new_param = inj.get('param').replace(self.tag, injection)
                else:
                    new_param = injection
                post_params[new_param] = old_value
            if inj.get('part') == 'value':
                if self.tag in post_params[inj.get('param')][inj.get('idx')]:
                    if post_params[inj.get('param')] == post_params[inj.get('param')][inj.get('idx')]:
                        post_params[inj.get('param')] = post_params[inj.get('param')].replace(self.tag, injection)
                    else:
                        post_params[inj.get('param')][inj.get('idx')] = post_params[inj.get('param')][inj.get('idx')].replace(self.tag, injection)
                else:
                    post_params[inj.get('param')][inj.get('idx')] = injection
        elif inj['field'] == 'GET':
            if inj.get('part') == 'param':
                old_value = get_params[inj.get('param')]
                del get_params[inj.get('param')]
                if self.tag in inj.get('param'):
                    new_param = inj.get('param').replace(self.tag, injection)
                else:
                    new_param = injection
                get_params[new_param] = old_value
            if inj.get('part') == 'value':
                if self.tag in get_params[inj.get('param')][inj.get('idx')]:
                    get_params[inj.get('param')][inj.get('idx')] = get_params[inj.get('param')][inj.get('idx')].replace(self.tag, injection)
                else:
                    get_params[inj.get('param')][inj.get('idx')] = injection
        elif inj['field'] == 'Header':
            injection = injection.replace('\n', '').replace('\r', '')
            if inj.get('part') == 'param':
                old_value = header_params[inj.get('param')]
                del header_params[inj.get('param')]
                if self.tag in inj.get('param'):
                    new_param = inj.get('param').replace(self.tag, injection)
                else:
                    new_param = injection
                header_params[new_param] = old_value
            if inj.get('part') == 'value':
                if self.tag in header_params[inj.get('param')]:
                    header_params[inj.get('param')] = header_params[inj.get('param')].replace(self.tag, injection)
                else:
                    header_params[inj.get('param')] = injection
        elif inj['field'] == 'Cookie':
            injection = injection.replace('\n', '').replace('\r', '')
            if inj.get('part') == 'param':
                old_value = cookie_params[inj.get('param')]
                del cookie_params[inj.get('param')]
                if self.tag in inj.get('param'):
                    new_param = inj.get('param').replace(self.tag, injection)
                else:
                    new_param = injection
                cookie_params[new_param] = old_value
            if inj.get('part') == 'value':
                if self.tag in cookie_params[inj.get('param')]:
                    cookie_params[inj.get('param')] = cookie_params[inj.get('param')].replace(self.tag, injection)
                else:
                    cookie_params[inj.get('param')] = injection
        if self.tag in self.base_url:
            log.debug(f'[URL] {url_params}')
        if get_params:
            log.debug(f'[GET] {get_params}')
        if post_params:
            log.debug(f'[POST] {post_params}')
        if len(header_params) > 1:
            log.debug(f'[HEDR] {header_params}')
        if len(cookie_params) > 1:
            log.debug(f'[COOK] {cookie_params}')
        if self.args.get('random_agent'):
            user_agent = get_agent()
        else:
            user_agent = self.args.get('user_agent')
        if 'user-agent' not in [p.lower() for p in header_params.keys()]:
            header_params['User-Agent'] = user_agent
        if self.args['delay']:
            time.sleep(self.args['delay'])
        try:
            if self.args.get('content_type') == "json":
                result = requests.request(method=self.http_method, url=url_params, params=get_params, json=post_params,
                                          headers=header_params, cookies=cookie_params, proxies=self.proxies,
                                          verify=self.args.get('verify_ssl')).text
            else:
                result = requests.request(method=self.http_method, url=url_params, params=get_params, data=post_params,
                                          headers=header_params, cookies=cookie_params, proxies=self.proxies,
                                          verify=self.args.get('verify_ssl')).text
        except requests.exceptions.ConnectionError as e:
            if e and e.args[0] and e.args[0].args[0] == 'Connection aborted.':
                log.log(25, 'Error: connection aborted, bad status line.')
                result = ""
            elif e and e.args[0] and 'Max retries exceeded' in e.args[0].args[0]:
                log.log(25, 'Error: max retries exceeded for a connection.')
                result = ""
            else:
                raise
        if self.args.get("log_response", False):
            log.debug(f"< {result}")
        return result

    def detected(self, technique, detail):
        pass
