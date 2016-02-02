import struct

def get(filepath):
    """
    Return (width, height) for a given img file content
    no requirements
    """
    height = -1
    width = -1
    
    with open(filepath, 'rb') as fhandle:
        head = fhandle.read(24)
        size = len(head)
        # handle GIFs
        if size >= 10 and head[:6] in ('GIF87a', 'GIF89a'):
            # Check to see if content_type is correct
            width, height = struct.unpack("<hh", head[6:10])
        # see png edition spec bytes are below chunk length then and finally the
        elif size >= 24 and head.startswith('\211PNG\r\n\032\n') and head[12:16] == 'IHDR':
            width, height = struct.unpack(">LL", head[16:24])
        # Maybe this is for an older PNG version.
        elif size >= 16 and head.startswith('\211PNG\r\n\032\n'):
            # Check to see if we have the right content type
            width, height = struct.unpack(">LL", head[8:16])
        # handle JPEGs
        elif size >= 2 and head.startswith('\377\330'):
            try:
                fhandle.seek(0) # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception: #IGNORE:W0703
                return
        # handle JPEG2000s
        elif size >= 12 and head.startswith('\x00\x00\x00\x0cjP  \r\n\x87\n'):
            fhandle.seek(48)
            height, width = struct.unpack('>LL', fhandle.read(8))
    return width, height

