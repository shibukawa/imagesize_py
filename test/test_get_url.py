import os
import shutil
import socket
import threading
import unittest

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler

import tempfile

import imagesize
from test.test_performance import (
    _box, _heif_with_property_order, _jpeg_segment, _jpeg_with_order,
)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


class RangeHandler(BaseHTTPRequestHandler):
    data = b""
    mode = "range"
    requests = []
    if_ranges = []
    bytes_sent = 0

    def log_message(self, format, *args):
        return

    def do_GET(self):
        range_header = self.headers.get("Range")
        type(self).requests.append(range_header)
        type(self).if_ranges.append(self.headers.get("If-Range"))
        data = type(self).data

        if type(self).mode == "404":
            self.send_response(404)
            self.end_headers()
            return

        if range_header and type(self).mode != "ignore":
            _, value = range_header.split("=", 1)
            start_value, end_value = value.split("-", 1)
            start = int(start_value)
            end = min(int(end_value), len(data) - 1)
            payload = data[start:end + 1]
            self.send_response(206)
            if type(self).mode == "malformed":
                self.send_header("Content-Range", "invalid")
            else:
                self.send_header("Content-Range", "bytes {}-{}/{}".format(start, end, len(data)))
            etag = '"v2"' if type(self).mode == "changed" and len(type(self).requests) > 1 else '"v1"'
            self.send_header("ETag", etag)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            type(self).bytes_sent += len(payload)
            self.wfile.write(payload)
            return

        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("ETag", '"v2"')
        self.end_headers()
        type(self).bytes_sent += len(data)
        self.wfile.write(data)


def _pick_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


def _start_server(handler):
    port = _pick_free_port()
    server = HTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server, thread, "http://127.0.0.1:{}/image".format(port)


def _large_heif():
    source = _heif_with_property_order(True)
    ftyp_size = int.from_bytes(source[:4], "big")
    return source[:ftyp_size] + _box(b"mdat", bytes(8 * 1024 * 1024)) + source[ftyp_size:]


def _fixture(name):
    with open(os.path.join(os.path.dirname(__file__), "images", name), "rb") as fhandle:
        return fhandle.read()


def test_get_http_url():
    imagedir = os.path.join(os.path.dirname(__file__), "images")

    tempdir = tempfile.mkdtemp()
    try:
        shutil.copy(os.path.join(imagedir, "test.jpg"), os.path.join(tempdir, "test.jpg"))

        cwd = os.getcwd()
        os.chdir(tempdir)
        try:
            port = _pick_free_port()
            server = HTTPServer(("127.0.0.1", port), QuietHandler)
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()

            try:
                assert imagesize.get("http://127.0.0.1:{}/test.jpg".format(port)) == (802, 670)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
        finally:
            os.chdir(cwd)
    finally:
        shutil.rmtree(tempdir)


def test_http_range_skips_large_heif_payload():
    RangeHandler.data = _large_heif()
    RangeHandler.mode = "range"
    RangeHandler.requests = []
    RangeHandler.if_ranges = []
    RangeHandler.bytes_sent = 0
    server, thread, url = _start_server(RangeHandler)
    try:
        assert imagesize.get(url) == (420, 630)
        assert len(RangeHandler.requests) == 2
        assert all(value and value.startswith("bytes=") for value in RangeHandler.requests)
        assert RangeHandler.bytes_sent <= 256 * 1024
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_http_range_ignored_falls_back_to_full_response():
    RangeHandler.data = _fixture("test.png")
    RangeHandler.mode = "ignore"
    RangeHandler.requests = []
    RangeHandler.if_ranges = []
    RangeHandler.bytes_sent = 0
    server, thread, url = _start_server(RangeHandler)
    try:
        assert imagesize.get(url) == (802, 670)
        assert RangeHandler.requests == ["bytes=0-8191"]
        assert RangeHandler.bytes_sent == len(RangeHandler.data)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_invalid_content_range_retries_with_full_get():
    RangeHandler.data = _fixture("test.png")
    RangeHandler.mode = "malformed"
    RangeHandler.requests = []
    RangeHandler.if_ranges = []
    RangeHandler.bytes_sent = 0
    server, thread, url = _start_server(RangeHandler)
    try:
        assert imagesize.get(url) == (802, 670)
        assert RangeHandler.requests == ["bytes=0-8191", None]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_changed_range_validator_retries_with_full_get():
    RangeHandler.data = _large_heif()
    RangeHandler.mode = "changed"
    RangeHandler.requests = []
    RangeHandler.if_ranges = []
    RangeHandler.bytes_sent = 0
    server, thread, url = _start_server(RangeHandler)
    try:
        assert imagesize.get(url) == (420, 630)
        assert RangeHandler.requests[-1] is None
        assert len(RangeHandler.requests) == 3
        assert RangeHandler.if_ranges[1] == '"v1"'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_jpeg_metadata_orders_stay_in_one_range_block():
    for exif_first in (True, False):
        RangeHandler.data = _jpeg_with_order(exif_first)
        RangeHandler.mode = "range"
        RangeHandler.requests = []
        RangeHandler.if_ranges = []
        RangeHandler.bytes_sent = 0
        server, thread, url = _start_server(RangeHandler)
        try:
            assert imagesize.get(url) == (20, 40)
            assert RangeHandler.requests == ["bytes=0-8191"]
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


def test_http_error_preserves_sentinel_behavior():
    RangeHandler.data = b""
    RangeHandler.mode = "404"
    RangeHandler.requests = []
    RangeHandler.if_ranges = []
    RangeHandler.bytes_sent = 0
    server, thread, url = _start_server(RangeHandler)
    try:
        assert imagesize.get(url) == (-1, -1)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_small_header_format_uses_initial_range_only():
    RangeHandler.data = _fixture("test.png") + bytes(8 * 1024 * 1024)
    RangeHandler.mode = "range"
    RangeHandler.requests = []
    RangeHandler.if_ranges = []
    RangeHandler.bytes_sent = 0
    server, thread, url = _start_server(RangeHandler)
    try:
        assert imagesize.get(url) == (802, 670)
        assert RangeHandler.requests == ["bytes=0-8191"]
        assert RangeHandler.bytes_sent == 8 * 1024
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_initial_range_expands_when_header_metadata_is_larger():
    padding = _jpeg_segment(0xe2, bytes(9 * 1024))
    source = b'\xff\xd8' + padding + _jpeg_with_order(True)[2:]
    RangeHandler.data = source
    RangeHandler.mode = "range"
    RangeHandler.requests = []
    RangeHandler.if_ranges = []
    RangeHandler.bytes_sent = 0
    server, thread, url = _start_server(RangeHandler)
    try:
        assert imagesize.get(url) == (20, 40)
        assert RangeHandler.requests == ["bytes=0-8191", "bytes=8192-65535"]
        assert RangeHandler.bytes_sent == len(source)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class GetUrlTest(unittest.TestCase):
    test_get_http_url = staticmethod(test_get_http_url)
    test_http_range_skips_large_heif_payload = staticmethod(test_http_range_skips_large_heif_payload)
    test_http_range_ignored_falls_back_to_full_response = staticmethod(
        test_http_range_ignored_falls_back_to_full_response
    )
    test_invalid_content_range_retries_with_full_get = staticmethod(test_invalid_content_range_retries_with_full_get)
    test_changed_range_validator_retries_with_full_get = staticmethod(
        test_changed_range_validator_retries_with_full_get
    )
    test_jpeg_metadata_orders_stay_in_one_range_block = staticmethod(test_jpeg_metadata_orders_stay_in_one_range_block)
    test_http_error_preserves_sentinel_behavior = staticmethod(test_http_error_preserves_sentinel_behavior)
    test_small_header_format_uses_initial_range_only = staticmethod(test_small_header_format_uses_initial_range_only)
    test_initial_range_expands_when_header_metadata_is_larger = staticmethod(
        test_initial_range_expands_when_header_metadata_is_larger
    )
