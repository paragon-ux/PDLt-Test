TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a write-ahead log (WAL) in Python with crash recovery. Provide an append(record: bytes) -> int function that appends a record prefixed with a 4-byte length, 4-byte CRC32 checksum, and 8-byte sequence number, returning its sequence number. Provide a recover() -> list[bytes] function that reads the log file from disk and returns all valid records, stopping at the first corrupted or truncated record. Provide a sync() function that forces an fsync to disk. Include a test that writes 100 records, closes the log, truncates the file mid-record to simulate a crash, reopens the log, and verifies that recover() returns exactly the intact records with correct checksums.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- WAL
- Python
- append(record: bytes) -> int
- recover() -> list[bytes]
- sync()
- 4-byte length
- 4-byte CRC32 checksum
- 8-byte sequence number
- 100 records
