IMPLEMENT a write-ahead log (WAL) system in Python with the following operations:
    The function named append takes a record of type bytes and returns an int sequence number. Each stored entry must be prefixed with a 4-byte length, a 4-byte CRC32 checksum, and an 8-byte sequence number.
    The function named recover reads the log file and returns a list[bytes] of all records that are valid according to the length, checksum, and sequence number, stopping at the first corrupted or truncated record.
    The function named sync forces an fsync to persist data to disk.
DESIGN a test that writes 100 records to the log, closes the log, truncates the file in the middle of a record to simulate a crash, reopens the log, and verifies that recover returns exactly the intact records with correct checksums.
