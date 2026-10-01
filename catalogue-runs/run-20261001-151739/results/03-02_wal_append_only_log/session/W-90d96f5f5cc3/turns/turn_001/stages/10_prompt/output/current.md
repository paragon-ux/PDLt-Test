ENTITIES: append(record: bytes) -> int, recover() -> list[bytes], sync(), 4-byte length, 4-byte CRC32 checksum, 8-byte sequence number, 100 records, write-ahead log (WAL), Python

IMPLEMENT a write-ahead log (WAL) in Python with crash recovery.

DEFINE FUNCTION append(record: bytes) -> int THAT
  PREPEND each record with a 4-byte length, a 4-byte CRC32 checksum, and an 8-byte sequence number.
  APPEND the formatted record to the log file.
  RETURN the assigned sequence number.

DEFINE FUNCTION recover() -> list[bytes] THAT
  READ the log file sequentially.
  FOR each record:
    READ the 4-byte length, the 4-byte CRC32 checksum, and the 8-byte sequence number.
    READ the record data of the specified length.
    VALIDATE the CRC32 checksum.
    IF checksum is valid THEN ADD the record data to the output list.
    ELSE STOP processing at the first corrupted or truncated record.
  RETURN the list of recovered records.

DEFINE FUNCTION sync() THAT
  PERFORM an fsync to ensure the log file is persisted to disk.

TEST the implementation BY
  OPENING a new WAL.
  WRITING 100 records using append().
  CLOSING the WAL.
  TRUNCATING the log file mid-record to simulate a crash.
  REOPENING the WAL.
  CALLING recover().
  VERIFY that recover() returns exactly the intact records with correct checksums.
