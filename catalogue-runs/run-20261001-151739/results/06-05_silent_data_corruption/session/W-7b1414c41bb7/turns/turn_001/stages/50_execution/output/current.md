```python
import struct

# Choose a standard size format to avoid native padding.
# '=I?d' uses native byte order with standard sizes and no padding.
# '<I?d' would use little‑endian byte order with standard sizes and no padding.
# Here we use '=' to keep the original endianness while removing padding.

_FORMAT = '=I?d'  # unsigned int, bool, double without padding

def pack_record(user_id: int, active: bool, score: float) -> bytes:
    """Pack a record consisting of a uint32, a boolean, and a float64.

    The explicit format string ``=I?d`` guarantees that the packed size is
    exactly 13 bytes (4 bytes for the unsigned int, 1 byte for the bool, and
    8 bytes for the double) with no automatic padding inserted by the native
    format.
    """
    return struct.pack(_FORMAT, user_id, active, score)

def unpack_record(data: bytes):
    """Unpack a record packed with :func:`pack_record`.

    The same ``=I?d`` format string is used for unpacking, ensuring that the
    offsets match the packed layout and the original values are recovered
    correctly.
    """
    return struct.unpack(_FORMAT, data)

# Simple test
if __name__ == "__main__":
    original = (42, True, 98.6)
    packed = pack_record(*original)
    recovered = unpack_record(packed)
    print(f"Original: {original}")
    print(f"Recovered: {recovered}")
    print(f"Match: {original == recovered}")
    print(f"Packed size: {len(packed)} bytes (expected: 13)")
```
