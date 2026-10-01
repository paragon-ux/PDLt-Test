import os
import struct
import crcmod
import fcntl

class WriteAheadLog:
    """Simple write-ahead log with crash recovery.

    Each record is stored as:
        4-byte big‑endian length (N)
        4-byte CRC32 of the payload
        8-byte big‑endian sequence number
        N bytes payload
    """

    def __init__(self, path: str):
        self.path = path
        self.file = open(path, "a+b")
        self.file.seek(0, os.SEEK_END)
        # Determine next sequence number based on existing file
        self.seq = self._init_seq()
        self.crc32 = crcmod.predefined.mkPredefinedCrcFun('crc-32')

    def _init_seq(self) -> int:
        """Scan existing log to find the last sequence number.
        Returns next sequence number (last+1) or 0 if file empty.
        """
        self.file.flush()
        self.file.seek(0)
        seq = 0
        while True:
            header = self.file.read(4 + 4 + 8)
            if len(header) < 16:
                break
            length, checksum, seq_num = struct.unpack(">I I Q", header)
            payload = self.file.read(length)
            if len(payload) < length:
                break
            seq = seq_num
        return seq + 1

    def append(self, record: bytes) -> int:
        """Append a record and return its sequence number."""
        length = len(record)
        checksum = self.crc32(record) & 0xffffffff
        seq_num = self.seq
        header = struct.pack(">I I Q", length, checksum, seq_num)
        self.file.write(header + record)
        self.seq += 1
        return seq_num

    def sync(self) -> None:
        """Force data to disk (fsync)."""
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self) -> None:
        self.file.close()

    def recover(self) -> list[bytes]:
        """Recover valid records from the log.
        Stops at first corrupted or truncated record.
        """
        recovered = []
        self.file.flush()
        self.file.seek(0)
        while True:
            header = self.file.read(4 + 4 + 8)
            if len(header) == 0:
                # Reached EOF cleanly
                break
            if len(header) < 16:
                # Truncated header
                break
            length, checksum, seq_num = struct.unpack(">I I Q", header)
            payload = self.file.read(length)
            if len(payload) < length:
                # Truncated payload
                break
            if (self.crc32(payload) & 0xffffffff) != checksum:
                # Corrupted payload
                break
            recovered.append(payload)
        return recovered

# Test scenario
if __name__ == "__main__":
    import random
    import tempfile

    # Create temporary log file
    with tempfile.TemporaryDirectory() as td:
        log_path = os.path.join(td, "wal.log")
        wal = WriteAheadLog(log_path)
        records = []
        for i in range(100):
            data = f"record-{i}".encode()
            records.append(data)
            wal.append(data)
        wal.sync()
        wal.close()

        # Truncate the file in the middle of the last record to simulate crash
        with open(log_path, "rb+") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            # Move back a random amount less than last record length + header
            truncate_at = size - random.randint(1, 20)
            f.truncate(truncate_at)

        # Reopen and recover
        wal2 = WriteAheadLog(log_path)
        recovered = wal2.recover()
        # The last record is likely corrupted/truncated; we expect 99 intact records
        expected = records[:-1]  # last record may be incomplete
        assert recovered == expected, f"Recovered {len(recovered)} records, expected {len(expected)}"
        print("Recovery successful, recovered", len(recovered), "records")
        wal2.close()
