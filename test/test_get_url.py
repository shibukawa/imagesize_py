import os
import shutil
import socket
import threading

try:
    from http.server import HTTPServer, SimpleHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler

import tempfile

import imagesize


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def _pick_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


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
