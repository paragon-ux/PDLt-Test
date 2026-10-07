# Wrong: writes the CRC but never checks it, so a corrupted record is returned.
import struct
import zlib


class WAL:
    def __init__(self, path):
        self.path = path
        self.seq = len(self.recover())

    def append(self, record):
        with open(self.path, "ab") as fh:
            fh.write(struct.pack("<IIQ", len(record), zlib.crc32(record), self.seq) + record)
        self.seq += 1
        return self.seq - 1

    def sync(self):
        pass

    def recover(self):
        try:
            data = open(self.path, "rb").read()
        except FileNotFoundError:
            return []
        out, pos = [], 0
        while pos + 16 <= len(data):
            length, _crc, _ = struct.unpack_from("<IIQ", data, pos)
            body = data[pos + 16:pos + 16 + length]
            if len(body) < length:
                break
            out.append(body)
            pos += 16 + length
        return out
