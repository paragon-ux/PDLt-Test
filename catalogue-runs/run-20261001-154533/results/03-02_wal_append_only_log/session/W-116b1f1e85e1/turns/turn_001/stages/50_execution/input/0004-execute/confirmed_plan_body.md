DEFINE the binary log file format as a sequence of records each consisting of:
    4-byte length, 4-byte CRC32 checksum, 8-byte sequence number, and the payload bytes
INITIALIZE a monotonically increasing sequence counter starting at zero
IMPLEMENT the append operation:
    OPEN the log file for binary appending
    INCREMENT the sequence counter and assign the new value as the record's sequence number
    CALCULATE the CRC32 of the payload
    ENCODE the length, checksum, and sequence number in the required binary layout
    WRITE the encoded header followed by the payload to the file
    RETURN the assigned sequence number
IMPLEMENT the sync operation:
    FLUSH any buffered writes to the underlying file descriptor
    INVOKE fsync to force the data to be persisted on disk
IMPLEMENT the recover operation:
    OPEN the log file for binary reading
    WHILE not at end of file:
        READ the 4-byte length field
        IF insufficient bytes are available THEN STOP iteration
        READ the 4-byte checksum and the 8-byte sequence number
        READ the payload of the indicated length
        IF insufficient bytes are available THEN STOP iteration
        COMPUTE the CRC32 of the payload
        IF the computed checksum does not match the stored checksum THEN STOP iteration
        APPEND the payload to the collection of recovered records
    RETURN the collection of recovered records
DESIGN a test to validate the WAL implementation:
    GENERATE 100 distinct byte records
    FOR each record in the generated set:
        CALL the append operation to write the record to the log
    CLOSE the log file
    SELECT a byte offset that falls inside the middle of a stored record
    TRUNCATE the log file at the selected offset to simulate a crash scenario
    REOPEN the log file
    CALL the recover operation to retrieve the list of intact records
    DETERMINE the expected subset of records that should remain valid prior to the truncation point
    ASSERT that the recovered list matches the expected subset exactly
    CLEANUP any temporary files created for the test
