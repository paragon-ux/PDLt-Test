"""Hidden tests for 03-02: a write-ahead log with crash recovery.

From the prompt:
- append(record: bytes) -> int returns the record's sequence number;
- each record is framed as a 4-byte length, a 4-byte CRC32 and an 8-byte
  sequence number, then the payload;
- recover() -> list[bytes] returns the valid records, stopping at the first
  corrupt or truncated one;
- sync() forces an fsync.

The candidate is a class with append and recover, built from a file path (a
positional argument, or a keyword whose name mentions path or file). Closing is
close() if the class has it. A fresh instance on the same path reads what an
earlier one wrote.

The frame layout is checked on disk:
- the file is exactly the sum of 16 + len(payload) per record;
- each frame's length field matches its payload, in either byte order;
- each CRC field matches the payload, in either byte order. The prompt doesn't
  say what the CRC covers beyond the record, so a CRC over the sequence number
  and payload is accepted too.
"""
TEST_SECONDS = 40


def CANDIDATES():
    return [c for c in classes_with("append", "recover")]


_COUNTER = [0]


def _path():
    import os

    _COUNTER[0] += 1
    path = os.path.abspath(f"hidden_wal_{os.getpid()}_{_COUNTER[0]}.log")
    if os.path.exists(path):
        os.remove(path)
    return path


def _open(cls, path):
    import inspect

    try:
        params = [p for p in inspect.signature(cls).parameters.values()]
    except (TypeError, ValueError):
        params = []
    for p in params:
        if any(w in p.name.lower() for w in ("path", "file", "name")):
            return cls(**{p.name: path})
    return cls(path)


def _close(log):
    for name in ("close", "flush"):
        method = getattr(log, name, None)
        if callable(method):
            method()
            if name == "close":
                return


def _records(n, seed=1):
    import random

    rng = random.Random(seed)
    return [bytes(rng.randrange(256) for _ in range(rng.randint(0, 40))) + f"#{i}".encode() for i in range(n)]


def test_append_returns_sequence_numbers_and_recover_reads_back(C):
    path = _path()
    log = _open(C, path)
    records = _records(100)
    seqs = [log.append(r) for r in records]
    assert all(isinstance(s, int) for s in seqs), seqs[:5]
    assert all(b - a == 1 for a, b in zip(seqs, seqs[1:])), "sequence numbers are not consecutive"
    if callable(getattr(log, "sync", None)):
        log.sync()
    _close(log)
    assert list(_open(C, path).recover()) == records


def test_frame_layout_on_disk(C):
    import struct
    import zlib

    path = _path()
    log = _open(C, path)
    records = _records(20, seed=2)
    seqs = [log.append(r) for r in records]
    _close(log)
    data = open(path, "rb").read()
    assert len(data) == sum(16 + len(r) for r in records), (len(data), sum(16 + len(r) for r in records))
    pos = 0
    for record, seq in zip(records, seqs):
        header = data[pos:pos + 16]
        lengths = {struct.unpack(f"{o}I", header[0:4])[0] for o in "<>"}
        assert len(record) in lengths, "length field"
        crcs = {struct.unpack(f"{o}I", header[4:8])[0] for o in "<>"}
        covered = {zlib.crc32(record), zlib.crc32(header[8:16] + record)}
        assert crcs & covered, "CRC field does not match the record"
        seq_fields = {struct.unpack(f"{o}Q", header[8:16])[0] for o in "<>"}
        assert seq in seq_fields, "sequence number field"
        pos += 16 + len(record)


def _written(C, seed):
    path = _path()
    log = _open(C, path)
    records = _records(100, seed=seed)
    for r in records:
        log.append(r)
    _close(log)
    return path, records


def test_truncated_tail_is_dropped(C):
    import os

    # Cut one byte off the end, inside the last header, and inside the last payload.
    for k, back in enumerate((1, None, None)):
        path, records = _written(C, seed=10 + k)
        size, last = os.path.getsize(path), 16 + len(records[-1])
        cut = size - 1 if back else (size - last + 5 if k == 1 else size - last + 16 + len(records[-1]) // 2)
        with open(path, "r+b") as fh:
            fh.truncate(cut)
        assert list(_open(C, path).recover()) == records[:-1], f"cut at {cut} of {size}"


def test_corrupt_record_stops_recovery(C):
    path, records = _written(C, seed=4)
    data = bytearray(open(path, "rb").read())
    offset = sum(16 + len(r) for r in records[:10])
    data[offset + 16] ^= 0xFF  # first payload byte of record 10 (payloads are never empty here)
    open(path, "wb").write(bytes(data))
    assert list(_open(C, path).recover()) == records[:10]


TESTS = [test_append_returns_sequence_numbers_and_recover_reads_back, test_frame_layout_on_disk,
         test_truncated_tail_is_dropped, test_corrupt_record_stops_recovery]
