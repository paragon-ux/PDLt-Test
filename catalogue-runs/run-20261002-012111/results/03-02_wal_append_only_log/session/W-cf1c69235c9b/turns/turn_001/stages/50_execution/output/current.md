import os
import struct
import zlib
from typing import List

class WriteAheadLog:
    """Simple write‑ahead log with length, CRC32, and sequence number.
    Records are stored as:
        4‑byte unsigned int – payload length (N)
        4‑byte unsigned int – CRC32 of payload
        8‑byte unsigned long long – sequence number
        N bytes – payload
    """

    def __init__(self, path: str):
        self.path = path
        self._fd = None
        # Determine next sequence number based on existing file
        self._next_seq = 1
        if os.path.exists(self.path):
            # Recover existing records to find last seq
            recovered = self.recover()
            if recovered:
                # Sequence numbers are stored; we read them during recover
                with open(self.path, "rb") as f:
                    while True:
                        header = f.read(4 + 4 + 8)
                        if len(header) < 16:
                            break
                        _, _, seq = struct.unpack('>IIQ', header)
                        self._next_seq = max(self._next_seq, seq + 1)
                        length = struct.unpack('>I', header[:4])[0]
                        f.seek(length, os.SEEK_CUR)
        # Open file descriptor for appends
        self._fd = open(self.path, "ab")

    def append(self, record: bytes) -> int:
        """Append a record and return its sequence number.
        The record is written as length, CRC32, sequence, payload.
        """
        if not isinstance(record, (bytes, bytearray)):
            raise TypeError("record must be bytes")
        length = len(record)
        crc = zlib.crc32(record) & 0xffffffff
        seq = self._next_seq
        self._next_seq += 1
        packed = struct.pack('>IIQ', length, crc, seq)
        self._fd.write(packed)
        self._fd.write(record)
        # Do not flush here; caller may invoke sync()
        return seq

    def sync(self) -> None:
        """Force data to disk using fsync."""
        if self._fd is None:
            raise RuntimeError("Log file not open")
        self._fd.flush()
        os.fsync(self._fd.fileno())

    def recover(self) -> List[bytes]:
        """Recover all valid records from the log file.
        Stops at the first truncated or corrupted record.
        """
        records: List[bytes] = []
        if not os.path.exists(self.path):
            return records
        with open(self.path, "rb") as f:
            while True:
                header = f.read(4 + 4 + 8)
                if len(header) == 0:
                    break  # EOF
                if len(header) < 16:
                    break  # Truncated header
                length, crc, seq = struct.unpack('>IIQ', header)
                payload = f.read(length)
                if len(payload) < length:
                    break  # Truncated payload
                if (zlib.crc32(payload) & 0xffffffff) != crc:
                    break  # Corrupted payload
                records.append(payload)
        return records

    def close(self) -> None:
        if self._fd:
            self._fd.close()
            self._fd = None

# ---------- Test ----------
import random
import tempfile

def _test_wal():
    # Create temporary directory for the WAL file
    with tempfile.TemporaryDirectory() as td:
        wal_path = os.path.join(td, "test.log")
        wal = WriteAheadLog(wal_path)
        written = []
        for i in range(100):
            payload = f"record-{i}".encode('utf-8')
            wal.append(payload)
            written.append(payload)
        wal.sync()
        wal.close()
        # Truncate the file in the middle of a record to simulate crash
        with open(wal_path, "r+b") as f:
            size = os.path.getsize(wal_path)
            # Choose a random offset that is not at a record boundary
            # Ensure we are at least 1 byte before end
            truncate_at = random.randint(1, size - 1)
            f.truncate(truncate_at)
        # Reopen and recover
        wal2 = WriteAheadLog(wal_path)
        recovered = wal2.recover()
        wal2.close()
        # Determine expected recovered records: iterate until truncation point
        expected = []
        offset = 0
        for payload in written:
            length = len(payload)
            record_size = 4 + 4 + 8 + length
            if offset + record_size > truncate_at:
                break
            expected.append(payload)
            offset += record_size
        assert recovered == expected, f"Recovered {len(recovered)} records, expected {len(expected)}"
        print("Test passed: recovered", len(recovered), "records")

if __name__ == "__main__":
    _test_wal()
