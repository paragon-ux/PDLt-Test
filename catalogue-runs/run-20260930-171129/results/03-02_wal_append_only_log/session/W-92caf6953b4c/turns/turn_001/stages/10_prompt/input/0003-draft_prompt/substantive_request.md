TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a write-ahead log (WAL) in Python with crash recovery. Required operations: append(record: bytes) -> int, which appends a record prefixed with a 4-byte length, 4-byte CRC32 checksum, and 8-byte sequence number and returns its sequence number; recover() -> list[bytes], which reads the log file from disk and returns all valid records, stopping at the first corrupted or truncated record; sync(), which forces an fsync to disk. Additionally, create a test that writes 100 records, closes the log, truncates the file mid-record to simulate a crash, reopens it, and verifies that recover() returns exactly the intact records with correct checksums.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- append
- record: bytes
- int
- recover
- list[bytes]
- sync
- fsync
- write-ahead log
- WAL
- crash recovery
- 4-byte length
- 4-byte CRC32 checksum
- 8-byte sequence number
- test
- 100 records
- truncate
- mid-record

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: crash recovery
