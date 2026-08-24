import argparse
import io
import os
import statistics
import struct
import timeit

import imagesize
import imagesize.imagesize as implementation


HERE = os.path.dirname(__file__)
IMAGE_DIR = os.path.join(HERE, "test", "images")
FILES = (
    "test.png",
    "test.jpg",
    "test.tiff",
    "test.gif",
    "test.jp2",
    "test.avif",
    "test.heic",
)


class CountingBytesIO(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.bytes_read = 0

    def read(self, size=-1):
        data = super().read(size)
        self.bytes_read += len(data)
        return data


class FakeResponse:
    def __init__(self, status, headers, data):
        self.status = status
        self.headers = headers
        self._data = data

    def getcode(self):
        return self.status

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class RangeTransport:
    def __init__(self, data):
        self.data = data
        self.requests = 0
        self.bytes_sent = 0

    def __call__(self, request):
        self.requests += 1
        range_header = request.get_header("Range")
        if not range_header:
            payload = self.data
            status = 200
            headers = {"Content-Length": str(len(payload))}
        else:
            start, end = (int(value) for value in range_header[6:].split("-"))
            end = min(end, len(self.data) - 1)
            payload = self.data[start:end + 1]
            status = 206
            headers = {
                "Content-Length": str(len(payload)),
                "Content-Range": "bytes {}-{}/{}".format(start, end, len(self.data)),
                "ETag": '"benchmark"',
            }
        self.bytes_sent += len(payload)
        return FakeResponse(status, headers, payload)


def _box(box_type, payload):
    return struct.pack(">L4s", len(payload) + 8, box_type) + payload


def _full_box(box_type, version, payload, flags=0):
    return _box(box_type, bytes([version]) + flags.to_bytes(3, "big") + payload)


def _large_avif():
    ftyp = _box(b"ftyp", b"avif\x00\x00\x00\x00avif")
    pitm = _full_box(b"pitm", 0, struct.pack(">H", 1))
    ispe = _full_box(b"ispe", 0, struct.pack(">LL", 630, 420))
    irot = _full_box(b"irot", 0, b"\x01")
    ipco = _box(b"ipco", ispe + irot)
    ipma = _full_box(b"ipma", 0, struct.pack(">LHBBB", 1, 1, 2, 1, 2))
    meta = _full_box(b"meta", 0, pitm + _box(b"iprp", ipco + ipma))
    payload_size = 8 * 1024 * 1024
    mdat = _box(b"mdat", bytes(payload_size))
    return ftyp + mdat + meta


def benchmark(number):
    print("file,size,bytes_read,median_us")
    for name in FILES:
        path = os.path.join(IMAGE_DIR, name)
        with open(path, "rb") as fhandle:
            data = fhandle.read()
        stream = CountingBytesIO(data)
        imagesize.get(stream)
        timings = timeit.repeat(lambda: imagesize.get(path), number=number, repeat=5)
        median_us = statistics.median(timings) * 1_000_000 / number
        print("{},{},{},{:.2f}".format(name, len(data), stream.bytes_read, median_us))

    transport = RangeTransport(_large_avif())
    original_urlopen = implementation.urlopen
    implementation.urlopen = transport
    try:
        result = imagesize.get("https://benchmark.invalid/image.avif")
    finally:
        implementation.urlopen = original_urlopen
    print()
    print("range_result={}, requests={}, bytes_transferred={}".format(
        result, transport.requests, transport.bytes_sent
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--number", type=int, default=10_000)
    benchmark(parser.parse_args().number)
