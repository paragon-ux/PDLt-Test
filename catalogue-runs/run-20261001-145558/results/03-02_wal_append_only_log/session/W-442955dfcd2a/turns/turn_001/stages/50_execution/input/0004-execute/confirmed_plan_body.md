INITIALIZE a write-ahead log (WAL) object with a target file path
DEFINE operation append(record: bytes) -> int that writes a 4-byte length, 4-byte CRC32, and 8-byte sequence number followed by the record
DEFINE operation sync() that forces an fsync on the underlying file descriptor
DEFINE operation recover() -> list[bytes] that reads sequentially, validates length, CRC32, and sequence order, and stops at the first corruption or truncation
CREATE a test scenario that:
    GENERATES 100 distinct records
    CALLS append for each record
    CLOSES the WAL
    TRUNCATES the log file at an arbitrary offset within the last record to simulate a crash
    REOPENS the WAL
    CALLS recover and captures the returned records
    VERIFIES that the recovered records equal the 100 intact records and that all checksums are valid
