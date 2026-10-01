DESIGN the WAL file format with per-record header consisting of a 4‑byte length field, a 4‑byte CRC32 checksum field, and an 8‑byte sequence number field, followed by the record payload.
IMPLEMENT a function append(record: bytes) -> int that
    CALCULATE the CRC32 checksum of the record payload.
    ENCODE the length, checksum, and sequence number as binary fields.
    CONCATENATE the header and payload.
    OPEN the log file in append binary mode.
    WRITE the concatenated record to the file.
    FLUSH the write buffer.
    RETURN the assigned sequence number.
IMPLEMENT a function sync() that
    OPEN the log file descriptor if not already open.
    CALL os.fsync on the descriptor to persist data to disk.
IMPLEMENT a function recover() -> list[bytes] that
    OPEN the log file in read binary mode.
    INITIALIZE an empty list for recovered records.
    WHILE not at end of file
        READ the 4‑byte length field.
        READ the 4‑byte checksum field.
        READ the 8‑byte sequence number field.
        READ the record payload of the specified length.
        VALIDATE that the checksum matches the payload.
        IF the validation succeeds
            APPEND the payload to the recovered list.
        ELSE
            BREAK processing at the first corrupted or truncated record.
    RETURN the list of recovered records.
DEVISE a test suite that
    CREATE a new WAL file.
    INVOKE append() 100 times with distinct record data.
    CLOSE the WAL file.
    TRUNCATE the file in the middle of a record to simulate a crash.
    REOPEN the WAL file.
    CALL recover().
    VERIFY that the returned list contains exactly the intact records with correct checksums.
PACKAGE the implementation and test suite into a Python module.
