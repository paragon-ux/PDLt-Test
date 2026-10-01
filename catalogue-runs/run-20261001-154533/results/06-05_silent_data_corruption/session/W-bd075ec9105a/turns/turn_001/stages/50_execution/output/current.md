```python
import struct

# Explicitly control padding to ensure a 13‑byte layout:
#   uint32 user_id   -> 4 bytes
#   bool   active    -> 1 byte
#   3 bytes padding   -> to align the following float64 on an 8‑byte boundary
#   float64 score    -> 8 bytes
# Use little‑endian standard size format ('<') and add explicit padding bytes.

# Packing format:
#   <   : little‑endian, standard sizes, no native alignment
#   I   : unsigned 4‑byte integer (uint32)
#   ?   : bool (treated as uint8)
#   3x  : three pad bytes (explicit padding)
#   d   : 8‑byte double (float64)
_PACK_FORMAT = '<I?3xd'

def pack_record(user_id: int, active: bool, score: float) -> bytes:
    """Pack a record into exactly 13 bytes.

    Parameters
    ----------
    user_id: int
        32‑bit unsigned integer.
    active: bool
        Boolean flag, stored as a single byte.
    score: float
        64‑bit floating‑point value.
    """
    return struct.pack(_PACK_FORMAT, user_id, active, score)

def unpack_record(data: bytes) -> tuple[int, bool, float]:
    """Unpack a 13‑byte record produced by :func:`pack_record`.

    Returns a tuple ``(user_id, active, score)``.
    """
    if len(data) != struct.calcsize(_PACK_FORMAT):
        raise ValueError(f"Expected {struct.calcsize(_PACK_FORMAT)} bytes, got {len(data)}")
    return struct.unpack(_PACK_FORMAT, data)

# Demonstration
if __name__ == "__main__":
    original = (42, True, 98.6)
    packed = pack_record(*original)
    recovered = unpack_record(packed)
    print(f"Original: {original}")
    print(f"Recovered: {recovered}")
    print(f"Match: {original == recovered}")
    print(f"Packed size: {len(packed)} bytes (expected: 13)")
```
