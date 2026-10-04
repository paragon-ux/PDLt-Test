# Correct with a different interface: WriteAheadLog(filename=...), big-endian
# frames, sequence numbers from 1, CRC over sequence number + payload, and a
# file handle opened per call.
import os
import struct
import zlib


class WriteAheadLog:
    def __init__(self, filename, start_seq=1):
        self.filename = filename
        self.seq = start_seq + len(self.recover())

    def append(self, record):
        seq_bytes = struct.pack(">Q", self.seq)
        frame = struct.pack(">I", len(record)) + struct.pack(">I", zlib.crc32(seq_bytes + record)) + seq_bytes + record
        with open(self.filename, "ab") as fh:
            fh.write(frame)
        self.seq += 1
        return self.seq - 1

    def sync(self):
        fd = os.open(self.filename, os.O_RDWR | getattr(os, "O_BINARY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def recover(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, "rb") as fh:
            blob = fh.read()
        out, i = [], 0
        while len(blob) - i >= 16:
            n, crc = struct.unpack(">II", blob[i:i + 8])
            seq_bytes, body = blob[i + 8:i + 16], blob[i + 16:i + 16 + n]
            if len(body) != n or zlib.crc32(seq_bytes + body) != crc:
                break
            out.append(body)
            i += 16 + n
        return out
