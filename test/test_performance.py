import io
import struct
import unittest
from unittest import mock

import imagesize
import imagesize.imagesize as implementation


def _box(box_type, payload):
    return struct.pack('>L4s', len(payload) + 8, box_type) + payload


def _full_box(box_type, version, payload, flags=0):
    return _box(box_type, bytes([version]) + flags.to_bytes(3, 'big') + payload)


def _exif_orientation(orientation=6):
    entry = struct.pack('<HHI', 0x0112, 3, 1) + struct.pack('<H', orientation) + b'\x00\x00'
    return b'\x00\x00\x00\x00' + b'II*\x00' + struct.pack('<L', 8) + struct.pack('<H', 1) + entry


def _jpeg_segment(marker, payload):
    return b'\xff' + bytes([marker]) + struct.pack('>H', len(payload) + 2) + payload


def _jpeg_with_order(exif_first):
    app1 = _jpeg_segment(0xe1, b'Exif\x00\x00' + _exif_orientation()[4:])
    sof = _jpeg_segment(0xc0, struct.pack('>BHHB', 8, 20, 40, 3))
    segments = app1 + sof if exif_first else sof + app1
    return b'\xff\xd8' + segments + b'\xff\xda'


def _tiff_header_metadata():
    entries = b''.join((
        struct.pack('<HHI4s', 256, 4, 1, struct.pack('<L', 40)),
        struct.pack('<HHI4s', 257, 4, 1, struct.pack('<L', 20)),
        struct.pack('<HHI4s', 274, 3, 1, struct.pack('<H', 6) + b'\x00\x00'),
    ))
    return b'II*\x00' + struct.pack('<L', 8) + struct.pack('<H', 3) + entries + b'\x00' * 64


def _heif_with_property_order(rotation_first):
    ftyp = _box(b'ftyp', b'avif\x00\x00\x00\x00avif')
    ispe = _full_box(b'ispe', 0, struct.pack('>LL', 630, 420))
    irot = _full_box(b'irot', 0, b'\x01')
    properties = irot + ispe if rotation_first else ispe + irot
    ipco = _box(b'ipco', properties)
    ipma = _full_box(b'ipma', 0, struct.pack('>LHBBB', 1, 1, 2, 1, 2))
    iprp = _box(b'iprp', ipco + ipma)
    pitm = _full_box(b'pitm', 0, struct.pack('>H', 1))
    return ftyp + _full_box(b'meta', 0, pitm + iprp)


def _heif_with_exif_order(metadata_first, split_extents=False):
    ftyp = _box(b'ftyp', b'avif\x00\x00\x00\x00avif')
    pitm = _full_box(b'pitm', 0, struct.pack('>H', 1))
    ispe = _full_box(b'ispe', 0, struct.pack('>LL', 630, 420))
    ipco = _box(b'ipco', ispe)
    ipma = _full_box(b'ipma', 0, struct.pack('>LHBB', 1, 1, 1, 1))
    iprp = _box(b'iprp', ipco + ipma)

    infe_payload = struct.pack('>HH4s', 2, 0, b'Exif')
    iinf = _full_box(b'iinf', 0, struct.pack('>H', 1) + _full_box(b'infe', 2, infe_payload))
    exif = _exif_orientation()
    extent_data = (
        struct.pack('>HHHH', 0, len(exif) // 2, len(exif) // 2, len(exif) - len(exif) // 2)
        if split_extents else struct.pack('>HH', 0, len(exif))
    )
    iloc_payload = (
        b'\x22\x00' + struct.pack('>H', 1) + struct.pack('>H', 2) +
        struct.pack('>H', 1) + struct.pack('>H', 0) +
        struct.pack('>H', 2 if split_extents else 1) + extent_data
    )
    iloc = _full_box(b'iloc', 1, iloc_payload)
    idat = _box(b'idat', exif)
    metadata = iinf + iloc + idat
    children = pitm + (metadata + iprp if metadata_first else iprp + metadata)
    return ftyp + _full_box(b'meta', 0, children)


def _jp2_with_header_order(resolution_first):
    signature = _box(b'jP  ', b'\r\n\x87\n')
    ihdr = _box(b'ihdr', struct.pack('>LL', 670, 802))
    resd = _box(b'resd', struct.pack('>HHHHbb', 72, 1, 72, 1, 0, 0))
    resolution = _box(b'res ', resd)
    children = resolution + ihdr if resolution_first else ihdr + resolution
    return signature + _box(b'jp2h', children)


class _CountingBytesIO(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.bytes_read = 0
        self.seek_history = []

    def read(self, size=-1):
        data = super().read(size)
        self.bytes_read += len(data)
        return data

    def seek(self, offset, whence=0):
        self.seek_history.append((offset, whence))
        return super().seek(offset, whence)


class PerformanceRegressionTest(unittest.TestCase):
    def test_large_png_only_reads_header(self):
        png = bytes.fromhex('89504e470d0a1a0a0000000d494844520000000100000001')
        stream = _CountingBytesIO(png + bytes(8 * 1024 * 1024 - len(png)))
        self.assertEqual(imagesize.get(stream), (1, 1))
        self.assertLessEqual(stream.bytes_read, 64)

    def test_jpeg_exif_and_sof_orders_use_one_forward_scan(self):
        for exif_first in (True, False):
            with self.subTest(exif_first=exif_first):
                stream = _CountingBytesIO(_jpeg_with_order(exif_first))
                self.assertEqual(imagesize.get(stream), (20, 40))
                self.assertEqual(stream.seek_history.count((0, 0)), 1)

    def test_already_read_header_is_reused_by_format_parsers(self):
        fixtures = (
            (_jpeg_with_order(True) + b'\x00' * 64, (20, 40)),
            (_tiff_header_metadata(), (20, 40)),
        )
        for source, expected in fixtures:
            with self.subTest(signature=source[:4]):
                stream = _CountingBytesIO(source)
                self.assertEqual(imagesize.get(stream), expected)
                self.assertEqual(stream.bytes_read, 64)

        jp2 = _jp2_with_header_order(False)
        stream = _CountingBytesIO(jp2)
        self.assertEqual(imagesize.get(stream), (802, 670))
        self.assertEqual(stream.bytes_read, len(jp2))

    def test_heif_property_order_is_independent(self):
        for rotation_first in (True, False):
            with self.subTest(rotation_first=rotation_first):
                self.assertEqual(imagesize.get(io.BytesIO(_heif_with_property_order(rotation_first))), (420, 630))

    def test_heif_exif_declaration_order_is_independent(self):
        for metadata_first in (True, False):
            for split_extents in (True, False):
                with self.subTest(metadata_first=metadata_first, split_extents=split_extents):
                    source = _heif_with_exif_order(metadata_first, split_extents)
                    self.assertEqual(imagesize.get(io.BytesIO(source)), (420, 630))

    def test_get_without_rotation_skips_heif_exif_item(self):
        source = _heif_with_exif_order(True, True)
        with mock.patch.object(
            implementation,
            '_read_tiff_orientation_stream',
            wraps=implementation._read_tiff_orientation_stream,
        ) as parser:
            self.assertEqual(
                imagesize.get(io.BytesIO(source), exif_rotation=False),
                (630, 420),
            )
        parser.assert_not_called()

    def test_heif_extended_and_zero_sized_boxes(self):
        source = _heif_with_property_order(True)
        ftyp_size = struct.unpack('>L', source[:4])[0]
        ftyp_payload = source[8:ftyp_size]
        extended_ftyp = struct.pack('>L4sQ', 1, b'ftyp', len(ftyp_payload) + 16) + ftyp_payload
        zero_sized_meta = b'\x00\x00\x00\x00' + source[ftyp_size + 4:]
        self.assertEqual(imagesize.get(io.BytesIO(extended_ftyp + zero_sized_meta)), (420, 630))

    def test_jp2_header_and_resolution_orders_share_one_scan(self):
        for resolution_first in (True, False):
            with self.subTest(resolution_first=resolution_first):
                info = imagesize.get_info(io.BytesIO(_jp2_with_header_order(resolution_first)))
                self.assertEqual((info.width, info.height), (802, 670))
                self.assertEqual((info.xdpi, info.ydpi), (2, 2))

    def test_invalid_iso_box_boundary_is_rejected(self):
        source = _heif_with_property_order(True)
        malformed = source[:4] + b'ftyp' + source[8:12]
        self.assertEqual(imagesize.get(io.BytesIO(malformed)), (-1, -1))

    def test_large_heif_mdat_is_skipped_and_metadata_is_parsed_once(self):
        source = _heif_with_property_order(True)
        ftyp_size = struct.unpack('>L', source[:4])[0]
        ftyp, meta = source[:ftyp_size], source[ftyp_size:]
        mdat = _box(b'mdat', bytes(8 * 1024 * 1024))
        stream = _CountingBytesIO(ftyp + mdat + meta)
        with mock.patch.object(
            implementation,
            '_read_heif_metadata_stream',
            wraps=implementation._read_heif_metadata_stream,
        ) as parser:
            self.assertEqual(imagesize.get(stream), (420, 630))
        self.assertEqual(parser.call_count, 1)
        self.assertLess(stream.bytes_read, 4096)

    def test_heif_top_level_boxes_are_traversed_once(self):
        source = _heif_with_property_order(True)
        with mock.patch.object(
            implementation,
            '_iter_iso_file_boxes',
            wraps=implementation._iter_iso_file_boxes,
        ) as iterator:
            self.assertEqual(imagesize.get(io.BytesIO(source)), (420, 630))
        top_level_calls = [
            call for call in iterator.call_args_list
            if len(call.args) >= 2 and call.args[1] == 0
        ]
        self.assertEqual(len(top_level_calls), 1)


if __name__ == '__main__':
    unittest.main()
