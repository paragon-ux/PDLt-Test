The original packing format string `'I?d'` uses the default native alignment. On most platforms, `struct` inserts padding after the `bool` to align the following `float64` on an 8‑byte boundary, so the total size becomes 16 bytes (4 for `I`, 1 for `?`, 3 bytes padding, 8 for `d`). This extra padding means the packed data is larger than the expected 13 bytes and, when unpacked, the fields can be mis‑interpreted because the layout does not match the intended compact layout.

**Why values may be read incorrectly**
- The padding bytes are not part of the logical record but are still present in the byte stream. If the receiver assumes a 13‑byte layout, it will read the wrong bytes for `score` (starting 1 byte too early) and the boolean may be shifted.
- Endianness is still respected, but the offset of `score` changes due to the padding, breaking the contract.

**Fix**
To enforce a packed layout without automatic padding, use the `struct` format character `'='` (standard size with native endianness) or explicitly add manual padding only where needed. The `'='` prefix disables the native alignment rules, giving a deterministic layout:
- `I` → 4 bytes (`uint32`)
- `?` → 1 byte (`bool`/`uint8`)
- `d` → 8 bytes (`float64`)
Total = 13 bytes, exactly as intended.

```python
import struct

# Use '=' to enforce standard size with no padding
_FORMAT = '=I?d'  # uint32, bool, float64 – total 13 bytes

def pack_record(user_id: int, active: bool, score: float) -> bytes:
    """Pack a record into exactly 13 bytes without padding."""
    return struct.pack(_FORMAT, user_id, active, score)

def unpack_record(data: bytes):
    """Unpack a 13‑byte record back into its components."""
    if len(data) != struct.calcsize(_FORMAT):
        raise ValueError(f"Data length {len(data)} does not match expected size {struct.calcsize(_FORMAT)}")
    return struct.unpack(_FORMAT, data)

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
