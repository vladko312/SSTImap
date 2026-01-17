import base64
import hashlib
import re
from utils.loggers import log


def quote(command):
    return command.replace("\\", "\\\\").replace('"', '\\"')


def compatible_url_safe_base64_encode(code):
    code_b64 = code if code is bytes else code.encode(encoding='UTF-8')
    code_b64 = base64.urlsafe_b64encode(code_b64).decode(encoding='UTF-8')
    return code_b64


def compatible_base64_encode(code):
    code_b64p = code if code is bytes else code.encode(encoding='UTF-8')
    code_b64p = base64.b64encode(code_b64p).decode(encoding='UTF-8')
    return code_b64p


def compatible_hex_encode(code):
    return (code if code is bytes else code.encode(encoding='UTF-8')).hex()


def compatible_getter(code, key):
    if type(code) in [str, list]:
        key = int(key)
    return code[key]


def chunk_seq(seq, n):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:n]
        seq = seq[n:]


def md5(data):
    return hashlib.md5(data).hexdigest()


def python_formatter(payload, data):
    format_data = data.copy()
    format_data['lens'] = {}
    for key in data:
        if type(data[key]) in [list, dict]:
            continue
        value = data[key] if data[key] is bytes else str(data[key])
        format_data.update({
            f'{key}_b64': compatible_url_safe_base64_encode(value),
            f'{key}_b64p': compatible_base64_encode(value)
        })
        # New length format
        format_data.update({
            f'{key}_len': len(value),
            f'{key}_len64': len(format_data[f'{key}_b64']),
            f'{key}_len64p': len(format_data[f'{key}_b64p'])
        })
        # Legacy length support
        if key[0] == 'c':
            format_data['lens'].update({
                'clen': format_data[f'{key}_len'],
                'clen64': format_data[f'{key}_len64'],
                'clen64p': format_data[f'{key}_len64p']
            })
        else:
            format_data['lens'][key] = format_data[f'{key}_len']
    return payload.format(**format_data)


filter_list = {
    "len": len,
    "str": str,
    "b64": compatible_base64_encode,
    "b64u": compatible_url_safe_base64_encode,
    "hex": compatible_hex_encode,
    "get": compatible_getter
}


def sstimap_formatter(payload, data):
    def _sstimap_process(match):
        value = data[match.group(1)]
        value = value if type(value) in [bytes, list, dict] else str(value)
        filters = match.group(2)
        if filters:
            filters = filters[1:].split(':')
            for f in filters:
                filter = f.split(',')
                if filter[0] in filter_list:
                    args = [] if len(filter) == 1 else filter[1:]
                    try:
                        value = filter_list[filter[0]](value, *args)
                    except Exception as e:
                        log.log(22, f'''Skipping formatting filter '{f}', error: {repr(e)}''')
                else:
                    log.log(22, f'''Skipping unknown formatting filter '{filter[0]}', payload might work incorrectly''')
        return value.decode(encoding='UTF-8') if value is bytes else str(value)
    return re.sub(r"SSTIMAP:([a-zA-Z0-9\-_.]+)((:[a-zA-Z0-9\-_.]+(,[a-zA-Z0-9\-_.])*)*);", _sstimap_process, payload)


formatters = {
    "sstimap": sstimap_formatter,
    "python": python_formatter,
    "default": python_formatter
}
