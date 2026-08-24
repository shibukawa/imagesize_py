import io
import os
import re
import struct
from collections import OrderedDict
from decimal import Decimal
from typing import BinaryIO, NamedTuple, Protocol, Tuple, Union, runtime_checkable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from xml.etree import ElementTree

_UNIT_KM = -3
_UNIT_100M = -2
_UNIT_10M = -1
_UNIT_1M = 0
_UNIT_10CM = 1
_UNIT_CM = 2
_UNIT_MM = 3
_UNIT_0_1MM = 4
_UNIT_0_01MM = 5
_UNIT_UM = 6
_UNIT_INCH = 6

_TIFF_TYPE_SIZES = {
  1: 1,
  2: 1,
  3: 2,
  4: 4,
  5: 8,
  6: 1,
  7: 1,
  8: 2,
  9: 4,
  10: 8,
  11: 4,
  12: 8,
}

_HEIF_BRANDS = {
    b'avif', b'avis',
    b'heic', b'heix', b'hevc', b'hevx',
    b'mif1', b'msf1',
}

_HEIF_IROT_TO_EXIF = {
    0: 1,
    1: 6,
    2: 3,
    3: 8,
}

_JPEG_NO_SOF_MARKERS = {0xc4, 0xc8, 0xcc}
_HTTP_INITIAL_RANGE_SIZE = 8 * 1024
_HTTP_RANGE_BLOCK_SIZE = 64 * 1024
_HTTP_RANGE_CACHE_BLOCKS = 8
_CONTENT_RANGE_RE = re.compile(r"bytes (\d+)-(\d+)/(\d+)$", re.IGNORECASE)


@runtime_checkable
class ReadSeekBinary(Protocol):
    def read(self, size: int = -1) -> bytes:
        ...

    def seek(self, offset: int, whence: int = 0) -> int:
        ...


PathInput = Union[str, bytes, os.PathLike]
FileInput = Union[PathInput, BinaryIO, ReadSeekBinary]


class ImageInfo(NamedTuple):
    width: int = -1
    height: int = -1
    rotation: int = -1
    xdpi: int = -1
    ydpi: int = -1
    colors: int = -1
    channels: int = -1


class _ImageMetadata(NamedTuple):
    width: int = -1
    height: int = -1
    rotation: int = -1
    xdpi: int = -1
    ydpi: int = -1
    colors: int = -1
    channels: int = -1


class _HttpRangeReader:
    """Small seekable HTTP reader backed by validated byte-range requests."""

    def __init__(self, url):
        self.url = url
        self._position = 0
        self._size = None
        self._validator = None
        self._blocks = OrderedDict()
        self._fallback = None
        self.closed = False

    def _request(self, start=None, end=None):
        headers = {"Accept-Encoding": "identity"}
        if start is not None:
            headers["Range"] = "bytes={}-{}".format(start, end)
            if self._validator:
                headers["If-Range"] = self._validator
        try:
            return urlopen(Request(self.url, headers=headers))
        except HTTPError as error:
            error.close()
            raise

    @staticmethod
    def _response_status(response):
        return getattr(response, "status", response.getcode())

    @staticmethod
    def _response_validator(response):
        etag = response.headers.get("ETag")
        if etag and not etag.startswith("W/"):
            return etag
        return response.headers.get("Last-Modified")

    def _download_full(self):
        with self._request() as response:
            if self._response_status(response) != 200:
                raise ValueError("Server did not provide a complete response")
            data = response.read()
        self._blocks.clear()
        self._fallback = io.BytesIO(data)
        self._size = len(data)
        self._validator = None

    def _load_block(self, block_index):
        if self._fallback is not None:
            return
        block = self._blocks.get(block_index)
        block_start = block_index * _HTTP_RANGE_BLOCK_SIZE
        offset = self._position - block_start
        if block is not None and offset < len(block):
            self._blocks.move_to_end(block_index)
            return

        start = block_start + (len(block) if block is not None else 0)
        if self._size is not None and start >= self._size:
            if block is None:
                self._blocks[block_index] = b""
            return
        if block_index == 0 and block is None:
            end = _HTTP_INITIAL_RANGE_SIZE - 1
        else:
            end = block_start + _HTTP_RANGE_BLOCK_SIZE - 1

        with self._request(start, end) as response:
            status = self._response_status(response)
            data = response.read()
            validator = self._response_validator(response)
            content_range = response.headers.get("Content-Range", "")

        if status == 200:
            self._blocks.clear()
            self._fallback = io.BytesIO(data)
            self._size = len(data)
            self._validator = None
            return

        matched = _CONTENT_RANGE_RE.fullmatch(content_range.strip()) if status == 206 else None
        if not matched:
            self._download_full()
            return

        response_start, response_end, total = (int(value) for value in matched.groups())
        if (response_start != start or response_end < response_start or
                response_end > end or len(data) != response_end - response_start + 1):
            self._download_full()
            return
        if self._size is not None and self._size != total:
            self._download_full()
            return
        if self._validator is not None and validator is not None and validator != self._validator:
            self._download_full()
            return

        self._size = total
        if self._validator is None:
            self._validator = validator
        self._blocks[block_index] = (block or b"") + data
        self._blocks.move_to_end(block_index)
        while len(self._blocks) > _HTTP_RANGE_CACHE_BLOCKS:
            self._blocks.popitem(last=False)

    def read(self, size=-1):
        if self.closed:
            raise ValueError("I/O operation on closed HTTP reader")
        if size == 0:
            return b""
        if self._fallback is not None:
            self._fallback.seek(self._position)
            data = self._fallback.read(size)
            self._position += len(data)
            return data

        self._load_block(self._position // _HTTP_RANGE_BLOCK_SIZE)
        if self._fallback is not None:
            return self.read(size)
        if size < 0:
            size = max(0, self._size - self._position)
        elif self._size is not None:
            size = min(size, max(0, self._size - self._position))

        chunks = []
        remaining = size
        while remaining > 0:
            block_index = self._position // _HTTP_RANGE_BLOCK_SIZE
            self._load_block(block_index)
            if self._fallback is not None:
                self._fallback.seek(self._position)
                chunk = self._fallback.read(remaining)
            else:
                block = self._blocks[block_index]
                offset = self._position % _HTTP_RANGE_BLOCK_SIZE
                chunk = block[offset:offset + remaining]
            if not chunk:
                break
            chunks.append(chunk)
            self._position += len(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def readline(self, size=-1):
        result = bytearray()
        while size < 0 or len(result) < size:
            value = self.read(1)
            if not value:
                break
            result += value
            if value == b"\n":
                break
        return bytes(result)

    def seek(self, offset, whence=0):
        if self.closed:
            raise ValueError("I/O operation on closed HTTP reader")
        if whence == os.SEEK_SET:
            position = offset
        elif whence == os.SEEK_CUR:
            position = self._position + offset
        elif whence == os.SEEK_END:
            if self._size is None:
                self._load_block(0)
            position = self._size + offset
        else:
            raise ValueError("invalid whence")
        if position < 0:
            raise ValueError("negative seek position")
        self._position = position
        return position

    def tell(self):
        return self._position

    def close(self):
        self.closed = True
        self._blocks.clear()
        if self._fallback is not None:
            self._fallback.close()


def _open_file(filepath: FileInput):
    if isinstance(filepath, str):
        if filepath.startswith(("http://", "https://")):
            return _HttpRangeReader(filepath), True
        return open(filepath, 'rb'), True
    if isinstance(filepath, (bytes, os.PathLike)):
        return open(filepath, 'rb'), True
    if isinstance(filepath, ReadSeekBinary):
        return filepath, False
    return open(filepath, 'rb'), True


def _convertToDPI(density, unit):
    if unit == _UNIT_KM:
        return int(density * 0.0000254 + 0.5)
    elif unit == _UNIT_100M:
        return int(density * 0.000254 + 0.5)
    elif unit == _UNIT_10M:
        return int(density * 0.00254 + 0.5)
    elif unit == _UNIT_1M:
        return int(density * 0.0254 + 0.5)
    elif unit == _UNIT_10CM:
        return int(density * 0.254 + 0.5)
    elif unit == _UNIT_CM:
        return int(density * 2.54 + 0.5)
    elif unit == _UNIT_MM:
        return int(density * 25.4 + 0.5)
    elif unit == _UNIT_0_1MM:
        return density * 254
    elif unit == _UNIT_0_01MM:
        return density * 2540
    elif unit == _UNIT_UM:
        return density * 25400
    return density


def _convertToPx(value):
    matched = re.match(r"(\d+(?:\.\d+)?)?([a-z]*)$", value)
    if not matched:
        raise ValueError("unknown length value: %s" % value)

    length, unit = matched.groups()
    length = Decimal(length)
    if unit == "":
        return float(length)
    elif unit == "cm":
        return float(length * Decimal("96") / Decimal("2.54"))
    elif unit == "mm":
        return float(length * Decimal("96") / Decimal("25.4"))
    elif unit == "in":
        return float(length * Decimal("96"))
    elif unit == "pc":
        return float(length * Decimal("96") / Decimal("6"))
    elif unit == "pt":
        return float(length * Decimal("96") / Decimal("72"))
    elif unit == "px":
        return float(length)

    raise ValueError("unknown unit type: %s" % unit)


def _read_orientation_from_exif_payload(exif_data):
    if len(exif_data) < 8:
        return -1
    endian_token = exif_data[:2]
    if endian_token == b'II':
        endian = '<'
    elif endian_token == b'MM':
        endian = '>'
    else:
        return -1

    try:
        first_ifd_offset = struct.unpack(endian + 'L', exif_data[4:8])[0]
    except struct.error:
        return -1
    if first_ifd_offset + 2 > len(exif_data):
        return -1

    try:
        ifd_count = struct.unpack(endian + 'H', exif_data[first_ifd_offset:first_ifd_offset + 2])[0]
    except struct.error:
        return -1
    cursor = first_ifd_offset + 2

    for _ in range(ifd_count):
        if cursor + 12 > len(exif_data):
            return -1
        try:
            tag, datatype, count, value = struct.unpack(endian + 'HHLL', exif_data[cursor:cursor + 12])
        except struct.error:
            return -1
        if tag == 0x0112 and datatype == 3 and count == 1:
            return int(value / 65536) if endian == '>' else value & 0xFFFF
        cursor += 12
    return -1


class _IsoFileBox(NamedTuple):
    offset: int
    size: int
    box_type: bytes
    header_size: int

    @property
    def payload_start(self):
        return self.offset + self.header_size

    @property
    def end(self):
        return self.offset + self.size


class _ItemLocation(NamedTuple):
    construction_method: int
    data_reference_index: int
    base_offset: int
    extents: tuple


def _read_exact(fhandle, size):
    data = fhandle.read(size)
    if len(data) != size:
        raise ValueError("Unexpected end of file")
    return data


def _stream_size(fhandle):
    position = fhandle.seek(0, os.SEEK_CUR)
    size = fhandle.seek(0, os.SEEK_END)
    fhandle.seek(position)
    return size


def _iter_iso_file_boxes(fhandle, start, end, head=None):
    offset = start
    while offset < end:
        if end - offset < 8:
            raise ValueError("Invalid ISO box header")
        if head is not None and offset + 8 <= len(head):
            size32, box_type = struct.unpack_from('>L4s', head, offset)
        else:
            cached = head[offset:] if head is not None and offset < len(head) else b''
            fhandle.seek(offset + len(cached))
            header = cached + _read_exact(fhandle, 8 - len(cached))
            size32, box_type = struct.unpack('>L4s', header)
        header_size = 8
        if size32 == 1:
            if head is not None and offset + 16 <= len(head):
                size = struct.unpack_from('>Q', head, offset + 8)[0]
            else:
                extended_offset = offset + 8
                cached = (head[extended_offset:] if head is not None and
                          extended_offset < len(head) else b'')
                fhandle.seek(extended_offset + len(cached))
                extended = cached + _read_exact(fhandle, 8 - len(cached))
                size = struct.unpack('>Q', extended)[0]
            header_size = 16
        elif size32 == 0:
            size = end - offset
        else:
            size = size32
        if size < header_size or offset + size > end:
            raise ValueError("Invalid ISO box size")
        yield _IsoFileBox(offset, size, box_type, header_size)
        offset += size


def _read_box_prefix(fhandle, box, size, head=None):
    available = box.end - box.payload_start
    if available < size:
        raise ValueError("Invalid ISO box payload")
    if head is not None and box.payload_start + size <= len(head):
        return head[box.payload_start:box.payload_start + size]
    cached = (head[box.payload_start:] if head is not None and
              box.payload_start < len(head) else b'')
    fhandle.seek(box.payload_start + len(cached))
    return cached + _read_exact(fhandle, size - len(cached))


def _parse_iinf(fhandle, box, item_types):
    header = _read_box_prefix(fhandle, box, min(8, box.end - box.payload_start))
    if len(header) < 6:
        raise ValueError("Invalid iinf box")
    version = header[0]
    entries_start = box.payload_start + (6 if version == 0 else 8)
    if entries_start > box.end:
        raise ValueError("Invalid iinf box")
    for entry in _iter_iso_file_boxes(fhandle, entries_start, box.end):
        if entry.box_type != b'infe':
            continue
        prefix_size = min(16, entry.end - entry.payload_start)
        prefix = _read_box_prefix(fhandle, entry, prefix_size)
        if len(prefix) < 12:
            continue
        infe_version = prefix[0]
        if infe_version == 2:
            item_id = struct.unpack('>H', prefix[4:6])[0]
            item_type = prefix[8:12]
        elif infe_version >= 3 and len(prefix) >= 16:
            item_id = struct.unpack('>L', prefix[4:8])[0]
            item_type = prefix[12:16]
        else:
            continue
        item_types[item_id] = item_type


def _parse_iloc(fhandle, box):
    payload_size = box.end - box.payload_start
    fhandle.seek(box.payload_start)
    data = _read_exact(fhandle, payload_size)
    if len(data) < 8:
        raise ValueError("Invalid iloc box")
    version = data[0]
    cursor = 4
    offset_size = data[cursor] >> 4
    length_size = data[cursor] & 0x0F
    cursor += 1
    base_offset_size = data[cursor] >> 4
    index_size = (data[cursor] & 0x0F) if version in (1, 2) else 0
    cursor += 1

    def take_int(size):
        nonlocal cursor
        if cursor + size > len(data):
            raise ValueError("Invalid iloc box")
        value = int.from_bytes(data[cursor:cursor + size], 'big') if size else 0
        cursor += size
        return value

    item_count = take_int(2 if version < 2 else 4)
    locations = {}
    for _ in range(item_count):
        item_id = take_int(2 if version < 2 else 4)
        construction_method = take_int(2) & 0x0F if version in (1, 2) else 0
        data_reference_index = take_int(2)
        base_offset = take_int(base_offset_size)
        extent_count = take_int(2)
        extents = []
        for _ in range(extent_count):
            if version in (1, 2) and index_size:
                take_int(index_size)
            extent_offset = take_int(offset_size)
            extent_length = take_int(length_size)
            extents.append((extent_offset, extent_length))
        locations[item_id] = _ItemLocation(
            construction_method, data_reference_index, base_offset, tuple(extents)
        )
    return locations


def _parse_ipma(fhandle, box, associations):
    payload_size = box.end - box.payload_start
    fhandle.seek(box.payload_start)
    data = _read_exact(fhandle, payload_size)
    if len(data) < 8:
        raise ValueError("Invalid ipma box")
    version = data[0]
    flags = int.from_bytes(data[1:4], 'big')
    large_index = bool(flags & 1)
    cursor = 4

    def take_int(size):
        nonlocal cursor
        if cursor + size > len(data):
            raise ValueError("Invalid ipma box")
        value = int.from_bytes(data[cursor:cursor + size], 'big')
        cursor += size
        return value

    entry_count = take_int(4)
    for _ in range(entry_count):
        item_id = take_int(2 if version == 0 else 4)
        association_count = take_int(1)
        indexes = []
        for _ in range(association_count):
            value = take_int(2 if large_index else 1)
            indexes.append(value & (0x7FFF if large_index else 0x7F))
        associations[item_id] = indexes


def _parse_iprp(fhandle, box, properties, associations):
    for child in _iter_iso_file_boxes(fhandle, box.payload_start, box.end):
        if child.box_type == b'ipco':
            for prop in _iter_iso_file_boxes(fhandle, child.payload_start, child.end):
                value = None
                if prop.box_type == b'ispe':
                    prefix = _read_box_prefix(fhandle, prop, 12)
                    value = struct.unpack('>LL', prefix[4:12])
                elif prop.box_type == b'irot':
                    prefix = _read_box_prefix(fhandle, prop, 5)
                    value = _HEIF_IROT_TO_EXIF.get(prefix[4] & 0x03, -1)
                properties.append((prop.box_type, value))
        elif child.box_type == b'ipma':
            _parse_ipma(fhandle, child, associations)


class _ExtentReader:
    def __init__(self, fhandle, extents):
        self._fhandle = fhandle
        self._extents = []
        logical_start = 0
        for file_offset, length in extents:
            if length <= 0:
                continue
            self._extents.append((logical_start, logical_start + length, file_offset))
            logical_start += length
        self._size = logical_start
        self._position = 0

    def seek(self, offset, whence=0):
        if whence == os.SEEK_SET:
            position = offset
        elif whence == os.SEEK_CUR:
            position = self._position + offset
        elif whence == os.SEEK_END:
            position = self._size + offset
        else:
            raise ValueError("invalid whence")
        if position < 0:
            raise ValueError("negative seek position")
        self._position = position
        return position

    def read(self, size=-1):
        if size < 0:
            size = self._size - self._position
        size = min(size, max(0, self._size - self._position))
        chunks = []
        remaining = size
        while remaining:
            for logical_start, logical_end, file_offset in self._extents:
                if logical_start <= self._position < logical_end:
                    available = min(remaining, logical_end - self._position)
                    self._fhandle.seek(file_offset + self._position - logical_start)
                    chunk = self._fhandle.read(available)
                    if not chunk:
                        return b"".join(chunks)
                    chunks.append(chunk)
                    self._position += len(chunk)
                    remaining -= len(chunk)
                    break
            else:
                break
        return b"".join(chunks)


def _read_tiff_orientation_stream(fhandle, base_offset=0):
    fhandle.seek(base_offset)
    header = fhandle.read(8)
    if len(header) < 8:
        return -1
    if header[:2] == b'II':
        endian = '<'
    elif header[:2] == b'MM':
        endian = '>'
    else:
        return -1
    try:
        if struct.unpack(endian + 'H', header[2:4])[0] != 42:
            return -1
        ifd_offset = struct.unpack(endian + 'L', header[4:8])[0]
        fhandle.seek(base_offset + ifd_offset)
        count = struct.unpack(endian + 'H', _read_exact(fhandle, 2))[0]
        for _ in range(count):
            entry = _read_exact(fhandle, 12)
            tag, datatype, value_count = struct.unpack(endian + 'HHI', entry[:8])
            if tag == 0x0112 and datatype == 3 and value_count == 1:
                return struct.unpack(endian + 'H', entry[8:10])[0]
    except (struct.error, ValueError):
        return -1
    return -1


def _read_heif_metadata_stream(fhandle, *, read_rotation=True, head=None):
    """Read HEIF metadata after locating ftyp and meta in one top-level scan."""
    file_size = _stream_size(fhandle)
    is_heif = False
    meta_box = None
    for box in _iter_iso_file_boxes(fhandle, 0, file_size, head=head):
        if box.box_type == b'ftyp':
            if box.end - box.payload_start < 8:
                return -1, -1, -1, -1
            prefix = _read_box_prefix(fhandle, box, 8, head=head)
            major_brand = prefix[:4]
            is_heif = major_brand in _HEIF_BRANDS
            brand_offset = box.payload_start + 8
            while not is_heif and brand_offset + 4 <= box.end:
                if head is not None and brand_offset + 4 <= len(head):
                    brand = head[brand_offset:brand_offset + 4]
                else:
                    fhandle.seek(brand_offset)
                    brand = _read_exact(fhandle, 4)
                is_heif = brand in _HEIF_BRANDS
                brand_offset += 4
        elif box.box_type == b'meta':
            meta_box = box
        if is_heif and meta_box is not None:
            break
    if not is_heif or meta_box is None or meta_box.end - meta_box.payload_start < 4:
        return -1, -1, -1, -1

    primary_item_id = None
    properties = []
    associations = {}
    item_types = {}
    item_locations = {}
    idat_payload_start = None
    children_start = meta_box.payload_start + 4
    for box in _iter_iso_file_boxes(fhandle, children_start, meta_box.end, head=head):
        if box.box_type == b'pitm':
            prefix = _read_box_prefix(fhandle, box, min(8, box.end - box.payload_start))
            if len(prefix) >= 6:
                item_id_data = prefix[4:6] if prefix[0] == 0 else prefix[4:8]
                primary_item_id = int.from_bytes(item_id_data, 'big')
        elif box.box_type == b'iinf' and read_rotation:
            _parse_iinf(fhandle, box, item_types)
        elif box.box_type == b'iloc' and read_rotation:
            item_locations.update(_parse_iloc(fhandle, box))
        elif box.box_type == b'iprp':
            _parse_iprp(fhandle, box, properties, associations)
        elif box.box_type == b'idat' and read_rotation:
            idat_payload_start = box.payload_start

    target_indexes = associations.get(primary_item_id, list(range(1, len(properties) + 1)))
    width = height = property_rotation = exif_rotation = -1
    for index in target_indexes:
        if not 1 <= index <= len(properties):
            continue
        property_type, value = properties[index - 1]
        if property_type == b'ispe' and value is not None:
            width, height = value
        elif read_rotation and property_type == b'irot' and value is not None:
            property_rotation = value

    for item_id, item_type in item_types.items() if property_rotation == -1 else ():
        if item_type != b'Exif':
            continue
        location = item_locations.get(item_id)
        if location is None or location.data_reference_index != 0:
            continue
        if location.construction_method == 0:
            origin = location.base_offset
        elif location.construction_method == 1 and idat_payload_start is not None:
            origin = idat_payload_start + location.base_offset
        else:
            continue
        extents = [(origin + offset, length) for offset, length in location.extents]
        reader = _ExtentReader(fhandle, extents)
        offset_data = reader.read(4)
        if len(offset_data) != 4:
            continue
        tiff_offset = 4 + struct.unpack('>L', offset_data)[0]
        exif_rotation = _read_tiff_orientation_stream(reader, tiff_offset)
        if exif_rotation != -1:
            break

    return width, height, property_rotation, exif_rotation


def _is_rotation_swapped(rotation):
    return rotation in {5, 6, 7, 8}


def _detect_image_format(head):
    if len(head) >= 10 and head[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if len(head) >= 8 and head.startswith(b'\211PNG\r\n\032\n'):
        return 'png'
    if len(head) >= 2 and head.startswith(b'\377\330'):
        return 'jpeg'
    if len(head) >= 12 and head.startswith(b'\x00\x00\x00\x0cjP  \r\n\x87\n'):
        return 'jp2'
    if len(head) >= 8 and head[4:8] == b'ftyp':
        return 'iso'
    if len(head) >= 8 and head[:4] in (b'MM\x00*', b'II*\x00', b'II+\x00'):
        return 'tiff'
    if len(head) >= 5 and (head.startswith(b'<?xml') or head.startswith(b'<svg')):
        return 'svg'
    if head[:1] == b'P' and head[1:2] in b'123456':
        return 'netpbm'
    if len(head) >= 16 and head.startswith(b'RIFF') and head[8:12] == b'WEBP':
        return 'webp'
    if head.startswith(b'BM'):
        return 'bmp'
    return 'unknown'


def _read_png_dpi(fhandle, head=None):
    offset = 8
    while True:
        if head is not None and offset + 8 <= len(head):
            header = head[offset:offset + 8]
        else:
            fhandle.seek(offset)
            header = fhandle.read(8)
        if len(header) != 8:
            raise ValueError("Invalid PNG file")
        length, chunk_type = struct.unpack('>L4s', header)
        if chunk_type == b'pHYs':
            if length < 9:
                raise ValueError("Invalid PNG file")
            payload_start = offset + 8
            if head is not None and payload_start + 9 <= len(head):
                payload = head[payload_start:payload_start + 9]
            else:
                fhandle.seek(payload_start)
                payload = _read_exact(fhandle, 9)
            xdensity, ydensity, unit = struct.unpack('>LLB', payload)
            if unit:
                return (_convertToDPI(xdensity, _UNIT_1M),
                        _convertToDPI(ydensity, _UNIT_1M))
            return xdensity, ydensity
        if chunk_type in (b'IDAT', b'IEND'):
            return -1, -1
        offset += 12 + length


def _read_jpeg_metadata(fhandle, *, size, dpi, rotation, channels, head=None):
    width = height = xdpi = ydpi = orientation = channel_count = -1
    found_sof = False
    found_dpi = False
    found_rotation = False
    position = 2

    def done():
        needed_sof = not (size or channels) or found_sof
        needed_dpi = not dpi or found_dpi
        needed_rotation = not rotation or found_rotation
        return needed_sof and needed_dpi and needed_rotation

    # Parse markers already present in the format-detection buffer directly.
    # If a segment crosses the boundary, combine the cached prefix with only
    # the unread suffix and then continue on the original stream.
    while head is not None and position < len(head):
        marker_start = head.find(b'\xff', position)
        if marker_start == -1:
            position = len(head)
            break
        marker_cursor = marker_start + 1
        while marker_cursor < len(head) and head[marker_cursor] == 0xff:
            marker_cursor += 1
        if marker_cursor >= len(head):
            position = marker_start
            break
        marker = head[marker_cursor]
        position = marker_cursor + 1
        if marker in (0xd9, 0xda):
            position = -1
            break
        if marker == 0x01 or 0xd0 <= marker <= 0xd7:
            continue
        if position + 2 > len(head):
            position = marker_start
            break
        segment_size = struct.unpack_from('>H', head, position)[0]
        if segment_size < 2:
            raise ValueError("Invalid JPEG segment size")
        payload_size = segment_size - 2
        payload_start = position + 2
        payload_end = payload_start + payload_size

        read_size = 0
        if marker == 0xe0 and dpi:
            read_size = min(payload_size, 14)
        elif marker == 0xe1 and rotation:
            read_size = payload_size
        elif 0xc0 <= marker <= 0xcf and marker not in _JPEG_NO_SOF_MARKERS:
            read_size = min(payload_size, 6)

        payload = b''
        if read_size:
            cached_end = min(payload_start + read_size, len(head))
            payload = head[payload_start:cached_end]
            remaining = read_size - len(payload)
            if remaining:
                fhandle.seek(cached_end)
                payload += fhandle.read(remaining)

        if marker == 0xe0 and dpi:
            if len(payload) >= 12 and payload.startswith(b'JFIF\x00'):
                unit, xdensity, ydensity = struct.unpack('>BHH', payload[7:12])
                if unit in (0, 1):
                    xdpi, ydpi = xdensity, ydensity
                elif unit == 2:
                    xdpi = _convertToDPI(xdensity, _UNIT_CM)
                    ydpi = _convertToDPI(ydensity, _UNIT_CM)
                found_dpi = True
        elif marker == 0xe1 and rotation:
            if payload.startswith(b'Exif\x00\x00'):
                orientation = _read_orientation_from_exif_payload(payload[6:])
                found_rotation = orientation != -1
        elif 0xc0 <= marker <= 0xcf and marker not in _JPEG_NO_SOF_MARKERS:
            if len(payload) < 6:
                raise ValueError("Invalid JPEG file")
            height, width, channel_count = struct.unpack('>xHHB', payload[:6])
            found_sof = True

        position = payload_end
        if done():
            break

    if not done() and position >= 0:
        fhandle.seek(position)
    while True:
        if done() or position < 0:
            break
        marker_start = fhandle.read(1)
        while marker_start and marker_start != b'\xff':
            marker_start = fhandle.read(1)
        if not marker_start:
            break
        marker_byte = fhandle.read(1)
        while marker_byte == b'\xff':
            marker_byte = fhandle.read(1)
        if not marker_byte:
            break
        marker = marker_byte[0]
        if marker in (0xd9, 0xda):
            break
        if marker == 0x01 or 0xd0 <= marker <= 0xd7:
            continue
        try:
            segment_size = struct.unpack('>H', _read_exact(fhandle, 2))[0]
        except (struct.error, ValueError):
            raise ValueError("Invalid JPEG file")
        if segment_size < 2:
            raise ValueError("Invalid JPEG segment size")
        payload_size = segment_size - 2
        payload_start = fhandle.seek(0, os.SEEK_CUR)

        if marker == 0xe0 and dpi:
            payload = fhandle.read(min(payload_size, 14))
            if len(payload) >= 12 and payload.startswith(b'JFIF\x00'):
                unit, xdensity, ydensity = struct.unpack('>BHH', payload[7:12])
                if unit in (0, 1):
                    xdpi, ydpi = xdensity, ydensity
                elif unit == 2:
                    xdpi = _convertToDPI(xdensity, _UNIT_CM)
                    ydpi = _convertToDPI(ydensity, _UNIT_CM)
                found_dpi = True
        elif marker == 0xe1 and rotation:
            payload = fhandle.read(payload_size)
            if payload.startswith(b'Exif\x00\x00'):
                orientation = _read_orientation_from_exif_payload(payload[6:])
                found_rotation = orientation != -1
        elif 0xc0 <= marker <= 0xcf and marker not in _JPEG_NO_SOF_MARKERS:
            payload = fhandle.read(min(payload_size, 6))
            if len(payload) < 6:
                raise ValueError("Invalid JPEG file")
            height, width, channel_count = struct.unpack('>xHHB', payload[:6])
            found_sof = True

        fhandle.seek(payload_start + payload_size)
        if done():
            break

    if (size or channels) and not found_sof:
        raise ValueError("Invalid JPEG file")
    return _ImageMetadata(
        width if size else -1,
        height if size else -1,
        orientation if rotation else -1,
        xdpi if dpi else -1,
        ydpi if dpi else -1,
        -1,
        channel_count if channels else -1,
    )


def _inline_tiff_value(entry, endian, datatype):
    if datatype == 3:
        return struct.unpack(endian + 'H', entry[:2])[0]
    if datatype == 4:
        return struct.unpack(endian + 'L', entry[:4])[0]
    return None


def _read_tiff_metadata(fhandle, *, size, rotation, head=None):
    if head is not None and len(head) >= 16:
        header = head[:16]
    else:
        fhandle.seek(0)
        header = _read_exact(fhandle, 16)
    if header.startswith(b'MM\x00*'):
        endian, bigtiff = '>', False
    elif header.startswith(b'II*\x00'):
        endian, bigtiff = '<', False
    elif header.startswith(b'II+\x00'):
        endian, bigtiff = '<', True
    else:
        raise ValueError("Invalid TIFF file")

    if bigtiff:
        if struct.unpack(endian + 'H', header[4:6])[0] != 8:
            raise ValueError("Invalid BigTIFF file")
        ifd_offset = struct.unpack(endian + 'Q', header[8:16])[0]
        count_size = 8
        entry_size = 20
    else:
        ifd_offset = struct.unpack(endian + 'L', header[4:8])[0]
        count_size = 2
        entry_size = 12

    if head is not None and ifd_offset + count_size <= len(head):
        count_data = head[ifd_offset:ifd_offset + count_size]
    else:
        fhandle.seek(ifd_offset)
        count_data = _read_exact(fhandle, count_size)
    entry_count = struct.unpack(endian + ('Q' if bigtiff else 'H'), count_data)[0]
    entry_offset = ifd_offset + count_size

    width = height = orientation = -1
    for _ in range(entry_count):
        if head is not None and entry_offset + entry_size <= len(head):
            entry = head[entry_offset:entry_offset + entry_size]
        else:
            fhandle.seek(entry_offset)
            entry = _read_exact(fhandle, entry_size)
        entry_offset += entry_size
        tag, datatype = struct.unpack(endian + 'HH', entry[:4])
        value_field = entry[12:20] if bigtiff else entry[8:12]
        if tag == 256 and size:
            value = _inline_tiff_value(value_field, endian, datatype)
            if value is not None:
                width = value
        elif tag == 257 and size:
            value = _inline_tiff_value(value_field, endian, datatype)
            if value is not None:
                height = value
        elif tag == 274 and rotation:
            value = _inline_tiff_value(value_field, endian, datatype)
            if value is not None:
                orientation = value
        size_done = not size or (width != -1 and height != -1)
        rotation_done = not rotation or orientation != -1
        if size_done and rotation_done:
            break
    if size and (width == -1 or height == -1):
        raise ValueError("Invalid TIFF file: missing dimensions")
    return _ImageMetadata(width, height, orientation)


def _iter_jp2_boxes(fhandle, start, container_size=None, head=None):
    remaining = container_size
    box_start = start
    while remaining is None or remaining > 0:
        if remaining is not None and remaining < 8:
            raise ValueError("Invalid JPEG2000 box size")
        if head is not None and box_start + 8 <= len(head):
            header = head[box_start:box_start + 8]
        else:
            cached = (head[box_start:] if head is not None and
                      box_start < len(head) else b'')
            fhandle.seek(box_start + len(cached))
            header = cached + fhandle.read(8 - len(cached))
        if not header and remaining is None:
            return
        if len(header) != 8:
            raise ValueError("Invalid JPEG2000 box header")
        box_size, box_type = struct.unpack('>L4s', header)
        header_size = 8
        if box_size == 1:
            if head is not None and box_start + 16 <= len(head):
                box_size = struct.unpack_from('>Q', head, box_start + 8)[0]
            else:
                extended_offset = box_start + 8
                cached = (head[extended_offset:] if head is not None and
                          extended_offset < len(head) else b'')
                fhandle.seek(extended_offset + len(cached))
                extended = cached + _read_exact(fhandle, 8 - len(cached))
                box_size = struct.unpack('>Q', extended)[0]
            header_size = 16
        elif box_size == 0:
            box_size = remaining
        if box_size is None:
            payload_size = _stream_size(fhandle) - box_start - header_size
        else:
            if box_size < header_size or (remaining is not None and box_size > remaining):
                raise ValueError("Invalid JPEG2000 box size")
            payload_size = box_size - header_size
        payload_start = box_start + header_size
        yield box_type, payload_start, payload_size
        box_start = payload_start + payload_size
        if remaining is not None:
            remaining -= box_size


def _read_jp2_metadata(fhandle, *, size, dpi, head=None):
    jp2_header = None
    for box_type, payload_start, payload_size in _iter_jp2_boxes(fhandle, 0, head=head):
        if box_type == b'jp2h':
            jp2_header = (payload_start, payload_size)
            break
    if jp2_header is None:
        raise ValueError("Invalid JPEG2000 file")

    width = height = xdpi = ydpi = -1
    for box_type, payload_start, payload_size in _iter_jp2_boxes(
            fhandle, jp2_header[0], jp2_header[1], head=head):
        if box_type == b'ihdr' and size:
            if head is not None and payload_start + 8 <= len(head):
                dimensions = head[payload_start:payload_start + 8]
            else:
                cached = (head[payload_start:] if head is not None and
                          payload_start < len(head) else b'')
                fhandle.seek(payload_start + len(cached))
                dimensions = cached + _read_exact(fhandle, 8 - len(cached))
            height, width = struct.unpack('>LL', dimensions)
        elif box_type == b'res ' and dpi:
            for resolution_type, resolution_start, resolution_size in _iter_jp2_boxes(
                    fhandle, payload_start, payload_size, head=head):
                if resolution_type != b'resd':
                    continue
                if resolution_size < 10:
                    raise ValueError("Invalid JPEG2000 resolution box")
                if head is not None and resolution_start + 10 <= len(head):
                    resolution = head[resolution_start:resolution_start + 10]
                else:
                    cached = b''
                    if head is not None and resolution_start < len(head):
                        cached = head[resolution_start:]
                    fhandle.seek(resolution_start + len(cached))
                    resolution = cached + _read_exact(fhandle, 10 - len(cached))
                (y_numerator, y_denominator, x_numerator, x_denominator,
                 y_exponent, x_exponent) = struct.unpack('>HHHHbb', resolution)
                if x_denominator and y_denominator:
                    x_density = x_numerator / x_denominator * (10 ** x_exponent)
                    y_density = y_numerator / y_denominator * (10 ** y_exponent)
                    xdpi = _convertToDPI(x_density, _UNIT_1M)
                    ydpi = _convertToDPI(y_density, _UNIT_1M)
                break
        if (not size or width != -1) and (not dpi or xdpi != -1):
            break
    if size and (width == -1 or height == -1):
        raise ValueError("Invalid JPEG2000 image header box")
    return _ImageMetadata(width, height, -1, xdpi, ydpi)


def _read_svg_size(fhandle, head=None):
    try:
        prefix = head or b''
        if len(prefix) < 1024:
            fhandle.seek(len(prefix))
            prefix += fhandle.read(1024 - len(prefix))
        data = prefix.decode('utf-8')
        width = re.search(r'''[^-]width=(["'])(.*?)\1''', data).group(2)
        height = re.search(r'''[^-]height=(["'])(.*?)\1''', data).group(2)
    except Exception:
        raise ValueError("Invalid SVG file")
    return _convertToPx(width), _convertToPx(height)


def _read_netpbm_size(fhandle, head=None):
    data = bytearray(head or b'')
    cursor = 2

    def ensure_data():
        if cursor < len(data):
            return True
        fhandle.seek(len(data))
        chunk = fhandle.read(64)
        if not chunk:
            return False
        data.extend(chunk)
        return True

    values = []
    while len(values) < 2:
        if not ensure_data():
            raise ValueError("Invalid Netpbm file")
        value = bytes([data[cursor]])
        cursor += 1
        if value.isspace():
            continue
        if value == b'#':
            while True:
                if not ensure_data():
                    raise ValueError("Invalid Netpbm file")
                value = bytes([data[cursor]])
                cursor += 1
                if value == b'\n':
                    break
            continue
        if not value.isdigit():
            raise ValueError("Invalid character found in Netpbm file")
        digits = value
        while ensure_data():
            value = bytes([data[cursor]])
            cursor += 1
            if not value.isdigit():
                break
            digits += value
        values.append(int(digits))
        if value.isdigit() and len(values) < 2:
            raise ValueError("Invalid Netpbm file")
    return tuple(values)


def _read_image_metadata(fhandle, *, size=True, dpi=True, colors=True,
                         rotation=True, channels=True):
    if not any((size, dpi, colors, rotation, channels)):
        return _ImageMetadata()
    fhandle.seek(0)
    head = fhandle.read(64)
    image_format = _detect_image_format(head)

    if image_format == 'jpeg':
        if not any((size, dpi, rotation, channels)):
            return _ImageMetadata()
        return _read_jpeg_metadata(
            fhandle, size=size, dpi=dpi, rotation=rotation, channels=channels, head=head
        )
    if image_format == 'tiff':
        if not (size or rotation):
            return _ImageMetadata()
        return _read_tiff_metadata(fhandle, size=size, rotation=rotation, head=head)
    if image_format == 'jp2':
        if not (size or dpi):
            return _ImageMetadata()
        return _read_jp2_metadata(fhandle, size=size, dpi=dpi, head=head)
    if image_format == 'iso':
        if not (size or rotation):
            return _ImageMetadata()
        width, height, property_rotation, exif_rotation = _read_heif_metadata_stream(
            fhandle, read_rotation=rotation, head=head
        )
        orientation = property_rotation if property_rotation != -1 else exif_rotation
        return _ImageMetadata(
            width if size else -1,
            height if size else -1,
            orientation if rotation else -1,
        )
    if image_format == 'png':
        if len(head) < 26 or head[12:16] != b'IHDR':
            raise ValueError("Invalid PNG file")
        width, height = struct.unpack('>LL', head[16:24]) if size else (-1, -1)
        bit_depth, color_type = head[24], head[25]
        color_channels = {0: 1, 2: 3, 3: 1, 4: 1, 6: 3}.get(color_type)
        color_count = 2 ** (bit_depth * color_channels) if colors and color_channels else -1
        channel_count = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type, -1) if channels else -1
        xdpi, ydpi = _read_png_dpi(fhandle, head=head) if dpi else (-1, -1)
        return _ImageMetadata(width, height, -1, xdpi, ydpi, color_count, channel_count)
    if image_format == 'gif':
        width, height = struct.unpack('<hh', head[6:10]) if size else (-1, -1)
        color_count = -1
        if colors and len(head) >= 11 and head[10] & 0x80:
            color_count = 2 ** ((head[10] & 0x07) + 1)
        return _ImageMetadata(width, height, -1, -1, -1, color_count, 3 if channels else -1)
    if image_format == 'bmp':
        width, height = struct.unpack('<ll', head[18:26]) if size else (-1, -1)
        height = abs(height) if size else -1
        channel_count = -1
        if channels and len(head) >= 30:
            depth = struct.unpack('<H', head[28:30])[0]
            channel_count = 1 if depth <= 8 else 3 if depth == 24 else 4 if depth == 32 else -1
        return _ImageMetadata(width, height, channels=channel_count)
    if image_format == 'svg':
        width, height = _read_svg_size(fhandle, head=head) if size else (-1, -1)
        return _ImageMetadata(width, height)
    if image_format == 'netpbm':
        width, height = _read_netpbm_size(fhandle, head=head) if size else (-1, -1)
        return _ImageMetadata(width, height)
    if image_format == 'webp':
        width = height = -1
        if size and head[12:16] == b'VP8 ':
            width, height = struct.unpack('<HH', head[26:30])
        elif size and head[12:16] == b'VP8X':
            width = struct.unpack('<I', head[24:27] + b'\0')[0] + 1
            height = struct.unpack('<I', head[27:30] + b'\0')[0] + 1
        elif size and head[12:16] == b'VP8L':
            value = head[21:25]
            width = (((value[1] & 63) << 8) | value[0]) + 1
            height = (((value[3] & 15) << 10) | (value[2] << 2) | ((value[1] & 192) >> 6)) + 1
        elif size:
            raise ValueError("Unsupported WebP file")
        return _ImageMetadata(width, height)
    return _ImageMetadata()

  
def get_info(filepath: FileInput, *, size: bool = True, dpi: bool = True, colors: bool = True,
             exif_rotation: bool = True, channels: bool = True) -> ImageInfo:
    fhandle, should_close = _open_file(filepath)
    try:
        metadata = _read_image_metadata(
            fhandle,
            size=size,
            dpi=dpi,
            colors=colors,
            rotation=size,
            channels=channels,
        )
        width, height = metadata.width, metadata.height
        if exif_rotation and _is_rotation_swapped(metadata.rotation):
            width, height = height, width
        return ImageInfo(
            width=width,
            height=height,
            rotation=metadata.rotation,
            xdpi=metadata.xdpi,
            ydpi=metadata.ydpi,
            colors=metadata.colors,
            channels=metadata.channels,
        )
    finally:
        if should_close:
            fhandle.close()


def get(filepath: FileInput, *, exif_rotation: bool = True) -> Tuple[int, int]:
    """
    Return (width, height) for a given img file content.
    Set exif_rotation=False to return stored dimensions as-is.
    :type filepath: Union[bytes, str, pathlib.Path]
    :rtype Tuple[int, int]
    """
    try:
        fhandle, should_close = _open_file(filepath)
        try:
            metadata = _read_image_metadata(
                fhandle,
                size=True,
                dpi=False,
                colors=False,
                rotation=exif_rotation,
                channels=False,
            )
        finally:
            if should_close:
                fhandle.close()
    except Exception:
        return -1, -1
    width, height = metadata.width, metadata.height
    if exif_rotation and _is_rotation_swapped(metadata.rotation):
        width, height = height, width
    return width, height


def getDPI(filepath: FileInput) -> Tuple[int, int]:
    """
    Return (x DPI, y DPI) for a given img file content
    no requirements
    :type filepath: Union[bytes, str, pathlib.Path]
    :rtype Tuple[int, int]
    """
    try:
        fhandle, should_close = _open_file(filepath)
        try:
            metadata = _read_image_metadata(
                fhandle,
                size=False,
                dpi=True,
                colors=False,
                rotation=False,
                channels=False,
            )
        finally:
            if should_close:
                fhandle.close()
    except Exception:
        return -1, -1
    return metadata.xdpi, metadata.ydpi
