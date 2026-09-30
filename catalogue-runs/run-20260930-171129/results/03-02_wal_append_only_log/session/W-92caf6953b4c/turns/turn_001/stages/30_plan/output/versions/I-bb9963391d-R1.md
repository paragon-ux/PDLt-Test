DEFINE a WriteAheadLog class managing a log file
IMPLEMENT method append(record: bytes) -> int that:
CALCULATE record length, CRC32 checksum, and next sequence number
WRITE 4-byte length, 4-byte checksum, 8-byte sequence number, then record bytes to the file
FLUSH and optionally CALL sync() to force persistence
RETURN the assigned sequence number
IMPLEMENT method sync() that forces an fsync on the underlying file descriptor
IMPLEMENT method recover() -> list[bytes] that:
OPEN the log file for reading
REPEAT reading records sequentially until EOF or corruption:
READ 4-byte length; IF insufficient bytes STOP
READ 4-byte checksum and 8-byte sequence number
READ the payload of the specified length; IF insufficient bytes STOP
VALIDATE checksum; IF mismatch STOP
APPEND payload to result list
RETURN the list of valid payloads
CREATE a test routine that:
INSTANTIATE a WriteAheadLog on a temporary file
FOR i FROM 1 TO 100:
CALL append(b"record-%d" % i)
CLOSE the log
TRUNCATE the file at a random offset inside the last record to simulate a crash
REOPEN the WriteAheadLog and CALL recover()
VERIFY that the recovered list contains exactly the intact records preceding the truncation and that each record’s checksum is correct
