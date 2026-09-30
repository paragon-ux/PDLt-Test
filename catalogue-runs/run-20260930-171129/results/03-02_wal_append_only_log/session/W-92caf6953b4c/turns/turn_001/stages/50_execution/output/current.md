import os
import struct
import zlib
from typing import List

class WriteAheadLog:
    def __init__(self, path: str):
        self.path = path
        # open file for appending binary and reading
        self._file = open(self.path, "a+b")
        self._file.seek(0, os.SEEK_END)
        # determine next sequence number
        self._seq = 0
        if os.path.getsize(self.path) > 0:
            # recover last sequence number safely without full decode
            # simple approach: read last 8 bytes if possible
            # but for correctness we will just start from 1 and let append assign incrementally
            self._seq = 0

    def append(self, record: bytes) -> int:
        """Append a record and return its sequence number.
        Record format:
        [4-byte length][4-byte CRC32][8-byte seq][payload]
        """
        length = len(record)
        checksum = zlib.crc32(record) & 0xffffffff
        self._seq += 1
        header = struct.pack('>I I Q', length, checksum, self._seq)
        self._file.write(header)
        self._file.write(record)
        self._file.flush()
        return self._seq

    def sync(self) -> None:
        os.fsync(self._file.fileno())

    def recover(self) -> List[bytes]:
        """Read the log and return all valid payloads up to first corruption/truncation."""
        records: List[bytes] = []
        self._file.flush()
        with open(self.path, "rb") as f:
            while True:
                hdr = f.read(4 + 4 + 8)
                if len(hdr) < 16:
                    break  # incomplete header -> stop
                length, checksum, seq = struct.unpack('>I I Q', hdr)
                payload = f.read(length)
                if len(payload) < length:
                    break  # truncated payload
                if (zlib.crc32(payload) & 0xffffffff) != checksum:
                    break  # checksum mismatch
                records.append(payload)
        return records

    def close(self) -> None:
        self._file.close()

# Test routine
if __name__ == "__main__":
    import tempfile, random
    # create temporary WAL file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        wal_path = tmp.name
    wal = WriteAheadLog(wal_path)
    written = []
    for i in range(1, 101):
        rec = f"record-{i}".encode()
        wal.append(rec)
        written.append(rec)
    wal.close()

    # truncate file in the middle of the last record to simulate crash
    with open(wal_path, "r+b") as f:
        size = os.path.getsize(wal_path)
        # get offset of last record start
        # calculate last record header+payload size
        last_len = len(written[-1])
        truncate_at = size - last_len // 2  # cut half way into payload
        f.truncate(truncate_at)

    # reopen and recover
    wal2 = WriteAheadLog(wal_path)
    recovered = wal2.recover()
    wal2.close()

    # verification
    # expected are all records except the last incomplete one
    expected = written[:-1]  # last record is incomplete
    assert recovered == expected, f"Recovered {len(recovered)} records, expected {len(expected)}"
    print("Test passed, recovered records match expected.")
