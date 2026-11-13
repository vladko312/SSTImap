import os
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import patch

from core.channel import Channel
from core.data_type import load_data_types
from utils.raw_request import RawRequestError, apply_raw_request, parse_raw_request


class RawRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_data_types()

    def parse(self, content, force_ssl=False):
        descriptor, path = tempfile.mkstemp()
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
            return parse_raw_request(path, force_ssl=force_ssl)
        finally:
            os.unlink(path)

    def test_parses_relative_post_request(self):
        request = self.parse(
            b"POST /profile?preview=1 HTTP/1.1\r\n"
            b"Host: example.test:8080\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"Cookie: session=abc; theme=dark\r\n"
            b"Content-Length: 13\r\n\r\n"
            b"display_name=*"
        )
        self.assertEqual("http://example.test:8080/profile?preview=1", request["url"])
        self.assertEqual("POST", request["method"])
        self.assertEqual(["display_name=*"], request["data"])
        self.assertEqual(["session=abc; theme=dark"], request["cookies"])
        self.assertNotIn("Content-Length: 13", request["headers"])
        self.assertIn("Content-Type: application/x-www-form-urlencoded", request["headers"])

    def test_force_ssl_and_lf_line_endings(self):
        request = self.parse(b"GET /page?name=* HTTP/1.1\nHost: example.test\n\n", force_ssl=True)
        self.assertEqual("https://example.test/page?name=*", request["url"])

    def test_absolute_url_does_not_require_host(self):
        request = self.parse(b"GET https://example.test/page?name=* HTTP/1.1\r\nAccept: */*\r\n\r\n")
        self.assertEqual("https://example.test/page?name=*", request["url"])

    def test_rejects_relative_url_without_host(self):
        with self.assertRaises(RawRequestError):
            self.parse(b"GET /page HTTP/1.1\r\nAccept: */*\r\n\r\n")

    def test_explicit_arguments_override_request(self):
        args = {
            "url": "https://override.test/",
            "method": "PUT",
            "data": ["cli=*"],
            "headers": ["X-Test: cli"],
            "cookies": ["cli=yes"],
        }
        request = {
            "url": "http://raw.test/",
            "method": "POST",
            "data": ["raw=*"],
            "headers": ["X-Raw: yes"],
            "cookies": ["raw=yes"],
        }
        merged = apply_raw_request(args, request)
        self.assertEqual("https://override.test/", merged["url"])
        self.assertEqual("PUT", merged["method"])
        self.assertEqual(["cli=*"], merged["data"])
        self.assertEqual(["X-Raw: yes", "X-Test: cli"], merged["headers"])
        self.assertEqual(["raw=yes", "cli=yes"], merged["cookies"])

    def test_parsed_request_is_sent_by_channel(self):
        request = self.parse(
            b"POST /profile HTTP/1.1\r\n"
            b"Host: example.test\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"Authorization: Bearer token\r\n"
            b"Cookie: session=abc\r\n\r\n"
            b"display_name=*"
        )
        args = apply_raw_request({
            "url": None,
            "method": None,
            "data": [],
            "headers": [],
            "cookies": [],
            "marker": "*",
            "proxy": None,
            "data_type": "auto",
            "module_params": {},
            "injection_points": "QBHC",
            "verify_ssl": False,
            "random_agent": False,
            "user_agent": "SSTImap/test",
            "delay": 0,
            "log_response": False,
        }, request)

        class Response:
            status_code = 200
            headers = {}
            cookies = {}
            content = b"ok"
            text = "ok"
            encoding = "utf-8"
            history = []
            url = "http://example.test/profile"
            elapsed = timedelta(milliseconds=1)

        with patch("core.channel.requests.request", return_value=Response()) as send:
            Channel(args).req("PAYLOAD")
        call = send.call_args.kwargs
        self.assertEqual("POST", call["method"])
        self.assertEqual("http://example.test/profile", call["url"])
        self.assertEqual({"display_name": ["PAYLOAD"]}, call["data"])
        self.assertEqual("Bearer token", call["headers"]["Authorization"])
        self.assertEqual("abc", call["cookies"]["session"])

    def test_second_order_request_returns_only_check_response_and_timing(self):
        injection = self.parse(
            b"POST /profile HTTP/1.1\r\n"
            b"Host: example.test\r\n"
            b"Content-Type: application/x-www-form-urlencoded\r\n"
            b"Cookie: writer=yes\r\n\r\n"
            b"display_name=*"
        )
        check = self.parse(
            b"GET /profile/view HTTP/1.1\r\n"
            b"Host: example.test\r\n"
            b"Cookie: view=yes\r\n\r\n"
        )
        args = apply_raw_request({
            "url": None,
            "method": None,
            "data": [],
            "headers": [],
            "cookies": [],
            "marker": "*",
            "proxy": None,
            "data_type": "auto",
            "module_params": {},
            "injection_points": "QBHC",
            "verify_ssl": False,
            "random_agent": False,
            "user_agent": "SSTImap/test",
            "delay": 0,
            "log_response": False,
            "check_request": check,
        }, injection)

        class InjectionResponse:
            text = "stored"

        class CheckResponse:
            status_code = 200
            headers = {}
            cookies = {}
            content = b"rendered PAYLOAD"
            text = "rendered PAYLOAD"
            encoding = "utf-8"
            history = []
            url = "http://example.test/profile/view"
            elapsed = timedelta(seconds=4)

        with patch("core.channel.requests.request", side_effect=[InjectionResponse(), CheckResponse()]) as send, \
                patch("core.channel.time.perf_counter", side_effect=[0, 10, 20, 24]):
            result, delta, response_vector = Channel(args).req("PAYLOAD")

        self.assertEqual("rendered PAYLOAD", result)
        self.assertEqual(4, delta)
        self.assertEqual("http://example.test/profile/view", response_vector["url"])
        self.assertEqual(2, send.call_count)
        injection_call, check_call = send.call_args_list
        self.assertEqual({"display_name": ["PAYLOAD"]}, injection_call.kwargs["data"])
        self.assertEqual({"writer": "yes"}, injection_call.kwargs["cookies"])
        self.assertEqual("http://example.test/profile/view", check_call.kwargs["url"])
        self.assertEqual({"view": "yes"}, check_call.kwargs["cookies"])


if __name__ == "__main__":
    unittest.main()
