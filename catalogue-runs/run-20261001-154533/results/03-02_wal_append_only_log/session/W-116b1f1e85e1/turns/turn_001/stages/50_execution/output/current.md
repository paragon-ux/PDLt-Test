import os
import struct
import zlib
from typing import List

class WriteAheadLog:
    """A simple write-ahead log (WAL) implementation.

    Each record is stored as:
        4-byte unsigned int – length of payload (big endian)
        4-byte unsigned int – CRC32 of payload (big endian)
        8-byte unsigned long long – sequence number (big endian)
        payload bytes – the record itself
    """

    HEADER_FMT = ">I I Q"  # length (uint32), crc32 (uint32), seq (uint64)
    HEADER_SIZE = struct.calcsize(HEADER_FMT)

    def __init__(self, path: str):
        self.path = path
        self._seq = 0
        # Open file in append+binary mode; create if not exists.
        self._file = open(self.path, "ab+")
        # Seek to end to initialize sequence counter from existing file.
        self._file.seek(0, os.SEEK_END)
        self._seq = self._recover_last_sequence()

    def _recover_last_sequence(self) -> int:
        """Read the file to find the highest sequence number already present.
        Used when reopening an existing log.
        """
        seq = 0
        try:
            with open(self.path, "rb") as f:
                while True:
                    header = f.read(self.HEADER_SIZE)
                    if len(header) < self.HEADER_SIZE:
                        break
                    length, crc, seq_num = struct.unpack(self.HEADER_FMT, header)
                    f.seek(length, os.SEEK_CUR)
                    seq = max(seq, seq_num)
        except FileNotFoundError:
            pass
        return seq

    def append(self, record: bytes) -> int:
        """Append a record to the log and return its sequence number.

        Parameters
        ----------
        record: bytes
            Payload to store.
        Returns
        -------
        int
            The assigned sequence number.
        """
        self._seq += 1
        length = len(record)
        crc = zlib.crc32(record) & 0xffffffff
        header = struct.pack(self.HEADER_FMT, length, crc, self._seq)
        self._file.write(header)
        self._file.write(record)
        return self._seq

    def sync(self) -> None:
        """Force the OS to flush buffered data to disk."""
        self._file.flush()
        os.fsync(self._file.fileno())

    def close(self) -> None:
        """Close the underlying file handle."""
        self._file.close()

    def recover(self) -> List[bytes]:
        """Recover valid records from the log.

        Stops at the first corrupted or truncated record.
        """
        records: List[bytes] = []
        with open(self.path, "rb") as f:
            while True:
                header_bytes = f.read(self.HEADER_SIZE)
                if len(header_bytes) < self.HEADER_SIZE:
                    break  # Truncated header
                length, stored_crc, seq_num = struct.unpack(self.HEADER_FMT, header_bytes)
                payload = f.read(length)
                if len(payload) < length:
                    break  # Truncated payload
                computed_crc = zlib.crc32(payload) & 0xffffffff
                if computed_crc != stored_crc:
                    break  # Corrupted checksum
                records.append(payload)
        return records

# ------------------- Test -------------------------------------------------
def _test_wal():
    import tempfile
    import random
    import shutil

    # Create temporary directory
    tmp_dir = tempfile.mkdtemp()
    try:
        log_path = os.path.join(tmp_dir, "wal.log")
        wal = WriteAheadLog(log_path)
        # Generate and append 100 distinct records
        records = [random.randbytes(random.randint(10, 50)) for _ in range(100)]
        for rec in records:
            wal.append(rec)
        wal.sync()
        wal.close()

        # Determine a truncation point inside a middle record
        with open(log_path, "rb") as f:
            # Read headers until we pass half of the records
            target_index = len(records) // 2
            offset = 0
            for i in range(target_index):
                header = f.read(WriteAheadLog.HEADER_SIZE)
                length, _, _ = struct.unpack(WriteAheadLog.HEADER_FMT, header)
                f.seek(length, os.SEEK_CUR)
                offset += WriteAheadLog.HEADER_SIZE + length
            # Now offset points to start of the (target_index)th record
            # Add a random amount within that record to truncate
            extra = random.randint(1, 5)
            trunc_offset = offset + extra
        # Truncate the file
        with open(log_path, "ab") as f:
            f.truncate(trunc_offset)

        # Recover
        wal2 = WriteAheadLog(log_path)
        recovered = wal2.recover()
        # Expected: records up to target_index (exclusive of the partially truncated one)
        expected = records[:target_index]
        assert recovered == expected, f"Recovered {len(recovered)} records, expected {len(expected)}"
        print("Test passed: recovered correct number of records")
    finally:
        shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    _test_wal()
