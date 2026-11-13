import re
import sys


class RawRequestError(ValueError):
    pass


def _read_request(path):
    try:
        if path == "-":
            return sys.stdin.buffer.read()
        with open(path, "rb") as stream:
            return stream.read()
    except OSError as error:
        raise RawRequestError(f"Unable to read raw HTTP request file '{path}': {error}")


def _split_request(raw):
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    match = re.search(br"\r?\n\r?\n", raw)
    if match:
        return raw[:match.start()], raw[match.end():]
    return raw, b""


def _parse_headers(lines):
    headers = []
    for line in lines:
        if line[:1] in (" ", "\t"):
            if not headers:
                raise RawRequestError("Invalid folded header in raw HTTP request")
            name, value = headers[-1]
            headers[-1] = (name, f"{value} {line.strip()}")
            continue
        if ":" not in line:
            raise RawRequestError(f"Invalid HTTP header: {line!r}")
        name, value = line.split(":", 1)
        name = name.strip()
        if not name or not re.match(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$", name):
            raise RawRequestError(f"Invalid HTTP header name: {name!r}")
        headers.append((name, value.strip()))
    return headers


def _request_url(target, headers, force_ssl):
    if re.match(r"^https?://", target, re.IGNORECASE):
        return target
    if not target.startswith("/"):
        raise RawRequestError("The request target must be an absolute URL or start with '/'")
    host = next((value for name, value in headers if name.lower() == "host"), None)
    if not host:
        raise RawRequestError("A Host header is required when the request target is relative")
    scheme = "https" if force_ssl else "http"
    return f"{scheme}://{host}{target}"


def _decode_body(body, headers):
    if not body:
        return ""
    content_type = next((value for name, value in headers if name.lower() == "content-type"), "")
    charset_match = re.search(r"(?:^|;)\s*charset\s*=\s*[\"']?([^;\"']+)", content_type,
                              re.IGNORECASE)
    encodings = [charset_match.group(1).strip()] if charset_match else []
    encodings.extend(["utf-8", "iso-8859-1"])
    for encoding in encodings:
        try:
            return body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    raise RawRequestError("Unable to decode the HTTP request body")


def parse_raw_request(path, force_ssl=False):
    """Parse a raw HTTP/1.x request file into SSTImap command-line values."""
    raw_headers, raw_body = _split_request(_read_request(path))
    try:
        header_text = raw_headers.decode("iso-8859-1")
    except UnicodeDecodeError as error:
        raise RawRequestError(f"Unable to decode HTTP headers: {error}")
    lines = header_text.splitlines()
    if not lines or not lines[0].strip():
        raise RawRequestError("Raw HTTP request is empty")
    request_line = lines[0].split()
    if len(request_line) != 3 or not request_line[2].upper().startswith("HTTP/"):
        raise RawRequestError(f"Invalid HTTP request line: {lines[0]!r}")
    method, target, _ = request_line
    if not re.match(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$", method):
        raise RawRequestError(f"Invalid HTTP method: {method!r}")

    parsed_headers = _parse_headers(lines[1:])
    url = _request_url(target, parsed_headers, force_ssl)
    headers = []
    cookies = []
    for name, value in parsed_headers:
        lower_name = name.lower()
        if lower_name == "cookie":
            cookies.append(value)
        elif lower_name not in ("content-length", "transfer-encoding"):
            headers.append(f"{name}: {value}")

    body = _decode_body(raw_body, parsed_headers)
    return {
        "url": url,
        "method": method.upper(),
        "headers": headers,
        "cookies": cookies,
        "body": body,
        "data": [body] if body else [],
    }


def apply_raw_request(args, request):
    """Merge a parsed request, giving explicitly supplied CLI values precedence."""
    if not args.get("url"):
        args["url"] = request["url"]
    if not args.get("method"):
        args["method"] = request["method"]
    if not args.get("data"):
        args["data"] = request["data"]
    args["headers"] = request["headers"] + (args.get("headers") or [])
    args["cookies"] = request["cookies"] + (args.get("cookies") or [])
    return args
