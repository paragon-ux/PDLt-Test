OTHERWISE: IMPLEMENT a write-ahead log (WAL) in Python with crash recovery.
OTHERWISE: PROVIDE an append(record: bytes) -> int function that appends a record prefixed with a 4-byte length, a 4-byte CRC32 checksum, and an 8-byte sequence number, returning its sequence number.
OTHERWISE: PROVIDE a recover() -> list[bytes] function that reads the log file from disk and returns all valid records, stopping at the first corrupted or truncated record.
OTHERWISE: PROVIDE a sync() function that forces an fsync to disk.
OTHERWISE: INCLUDE a test that writes 100 records, closes the log, truncates the file mid-record to simulate a crash, reopens the log, and verifies that recover() returns exactly the intact records with correct checksums.
