import os
import struct
import zlib
from typing import List

class WriteAheadLog:
    """Simple write-ahead log with per‑record header.

    Header format (big‑endian):
        uint32  length of payload
        uint32  CRC32 of payload
        uint64  monotonic sequence number
    """
    HEADER_FMT = ">IIQ"  # 4+4+8 bytes = 16
    HEADER_SIZE = struct.calcsize(HEADER_FMT)

    def __init__(self, path: str):
        self.path = path
        # Ensure the file exists
        open(self.path, "ab").close()
        self._seq = self._load_last_seq()
        self._fd = None

    def _load_last_seq(self) -> int:
        """Read the file to find the last written sequence number.
        If the file is empty or corrupted, the sequence starts at 0.
        """
        seq = 0
        try:
            with open(self.path, "rb") as f:
                while True:
                    header = f.read(self.HEADER_SIZE)
                    if len(header) < self.HEADER_SIZE:
                        break
                    length, _, seq_num = struct.unpack(self.HEADER_FMT, header)
                    # skip payload
                    f.seek(length, os.SEEK_CUR)
        except OSError:
            pass
        return seq

    def _open_fd(self):
        if self._fd is None:
            self._fd = os.open(self.path, os.O_WRONLY | os.O_APPEND)

    def append(self, record: bytes) -> int:
        """Append a record and return its sequence number.
        The record is stored as:
            [len][crc32][seq][payload]
        """
        self._open_fd()
        length = len(record)
        checksum = zlib.crc32(record) & 0xffffffff
        self._seq += 1
        header = struct.pack(self.HEADER_FMT, length, checksum, self._seq)
        os.write(self._fd, header + record)
        return self._seq

    def sync(self):
        """Force an fsync to ensure durability."""
        if self._fd is None:
            # open in read‑write mode just for syncing
            self._fd = os.open(self.path, os.O_WRONLY)
        os.fsync(self._fd)

    def recover(self) -> List[bytes]:
        """Read the log sequentially, returning all valid record payloads.
        Stops at the first corrupted or truncated record.
        """
        records: List[bytes] = []
        try:
            with open(self.path, "rb") as f:
                while True:
                    header = f.read(self.HEADER_SIZE)
                    if len(header) == 0:
                        break  # EOF reached cleanly
                    if len(header) < self.HEADER_SIZE:
                        break  # Truncated header
                    length, stored_crc, seq_num = struct.unpack(self.HEADER_FMT, header)
                    payload = f.read(length)
                    if len(payload) < length:
                        break  # Truncated payload
                    calc_crc = zlib.crc32(payload) & 0xffffffff
                    if calc_crc != stored_crc:
                        break  # Corrupt record
                    records.append(payload)
        except OSError:
            pass
        return records

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

# Test suite
if __name__ == "__main__":
    import random
    import tempfile

    # Create temporary WAL file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        wal_path = tmp.name
    wal = WriteAheadLog(wal_path)

    # Write 100 distinct records
    original_records = []
    for i in range(100):
        data = f"record-{i}".encode()
        original_records.append(data)
        wal.append(data)
    wal.sync()
    wal.close()

    # Truncate the file in the middle of the 101st record (which does not exist)
    # We'll truncate after the 50th record's payload to simulate a crash.
    # First, determine offset after 50 records.
    offset = 0
    with open(wal_path, "rb") as f:
        for idx in range(50):
            hdr = f.read(WriteAheadLog.HEADER_SIZE)
            if len(hdr) < WriteAheadLog.HEADER_SIZE:
                break
            length, _, _ = struct.unpack(WriteAheadLog.HEADER_FMT, hdr)
            offset += WriteAheadLog.HEADER_SIZE + length
            f.seek(length, os.SEEK_CUR)
    # Truncate half-way into next record's payload (if any)
    with open(wal_path, "rb+") as f:
        f.truncate(offset + 5)

    # Recover
    wal2 = WriteAheadLog(wal_path)
    recovered = wal2.recover()
    wal2.close()

    # Verify recovered records match the first 50 original records
    expected = original_records[:len(recovered)]
    assert recovered == expected, f"Recovered {len(recovered)} records, expected {len(expected)}"
    print("Recovery successful, recovered", len(recovered), "records")
