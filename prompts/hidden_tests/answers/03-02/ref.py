import os
import struct
import zlib

HEADER = struct.Struct("<IIQ")  # length, crc32(payload), sequence number


class WAL:
    def __init__(self, path):
        self.path = path
        self._next_seq = len(self.recover())
        # Drop any torn tail so new appends follow the last intact record.
        with open(path, "ab") as fh:
            fh.truncate(self._valid_bytes)
        self._fh = open(path, "ab")

    def append(self, record: bytes) -> int:
        seq = self._next_seq
        self._fh.write(HEADER.pack(len(record), zlib.crc32(record), seq) + record)
        self._next_seq += 1
        return seq

    def sync(self):
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def close(self):
        if self._fh and not self._fh.closed:
            self.sync()
            self._fh.close()

    def recover(self):
        records, pos = [], 0
        try:
            data = open(self.path, "rb").read()
        except FileNotFoundError:
            data = b""
        while pos + HEADER.size <= len(data):
            length, crc, _seq = HEADER.unpack_from(data, pos)
            payload = data[pos + HEADER.size:pos + HEADER.size + length]
            if len(payload) < length or zlib.crc32(payload) != crc:
                break
            records.append(payload)
            pos += HEADER.size + length
        self._valid_bytes = pos
        return records
