DEFINE the WAL file format as sequential records each consisting of a 4‑byte length field, a 4‑byte CRC32 checksum, an 8‑byte sequence number, and the payload bytes.
IMPLEMENT an append(record: bytes) -> int function that:
    CALCULATE the length of the payload
    ASSIGN the next sequence number
    COMPUTE the CRC32 checksum of the payload
    OPEN the WAL file in append binary mode
    WRITE the length, checksum, sequence number, and payload in the specified order
    RETURN the assigned sequence number
IMPLEMENT a sync() function that:
    OPEN the WAL file descriptor if not already open
    CALL os.fsync on the file descriptor to force data to disk
IMPLEMENT a recover() -> list[bytes] function that:
    OPEN the WAL file in binary read mode
    INITIALIZE an empty list for recovered records
    WHILE not at end of file:
        READ the 4‑byte length field
        IF insufficient bytes, STOP processing
        READ the 4‑byte checksum
        READ the 8‑byte sequence number
        READ the payload of the specified length
        IF payload length is incomplete, STOP processing
        VERIFY the CRC32 checksum matches the payload
        IF verification fails, STOP processing
        APPEND the payload to the recovered records list
    RETURN the list of recovered records
CREATE a test that:
    INSTANTIATE a new WAL instance
    FOR i from 1 to 100:
        CALL append with a distinct record payload
    CLOSE the WAL
    TRUNCATE the WAL file at a random byte offset that falls within a record to simulate a crash
    REOPEN the WAL
    CALL recover to retrieve the list of intact records
    COMPARE the recovered records with the subset of records written before the truncation point
    ASSERT that the number of recovered records matches the expected count and that each record’s checksum is valid
OPTIONALLY INCLUDE error handling that relies on the native runtime to propagate exceptions for unexpected I/O failures.
