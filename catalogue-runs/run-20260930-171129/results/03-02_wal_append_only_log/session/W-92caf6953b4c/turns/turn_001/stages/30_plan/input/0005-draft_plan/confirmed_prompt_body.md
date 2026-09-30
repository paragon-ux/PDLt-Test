NOTE: IMPLEMENT a write-ahead log (WAL) in Python with crash recovery.
NOTE: DEFINE operation append(record: bytes) -> int that appends a record prefixed with a 4-byte length, 4-byte CRC32 checksum, and 8-byte sequence number and returns its sequence number.
NOTE: DEFINE operation recover() -> list[bytes] that reads the log file from disk and returns all valid records, stopping at the first corrupted or truncated record.
NOTE: DEFINE operation sync() that forces an fsync to disk.
NOTE: CREATE a test that writes 100 records, closes the log, truncates the file mid-record to simulate a crash, reopens it, and verifies that recover() returns exactly the intact records with correct checksums.
