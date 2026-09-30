**Diagnostic Explanation**

The format string ``"I?d"`` is interpreted by the ``struct`` module using the *native* byte order, size and alignment (the default ``'@'`` prefix). On most platforms ``uint32`` (``I``) requires 4‑byte alignment, ``bool`` (``?``) is 1 byte, and ``float64`` (``d``) requires 8‑byte alignment. After the 1‑byte ``?`` field the compiler inserts 3 padding bytes so that the following ``d`` starts on an 8‑byte boundary. The resulting layout is:

```
offset  size  field
0       4     I  (user_id)
4       1     ?  (active)
5‑7    3     padding
8       8     d  (score)
```

Total size = 4 + 1 + 3 (padding) + 8 = **16 bytes**, not the expected 13. When unpacking with the same format the padded bytes are interpreted as part of the ``d`` value, leading to incorrect numbers.

**Alignment Rules**

* Native format (default ``'@'``) respects the C compiler's alignment for the host architecture.
* ``I`` – 4‑byte alignment.
* ``?`` – 1‑byte alignment.
* ``d`` – 8‑byte alignment, causing up‑to‑7 bytes of padding before it if the previous field’s size does not satisfy the alignment.

**Corrected Implementation**

To obtain a deterministic 13‑byte layout we must **disable native alignment** and specify the exact padding ourselves. Using the ``'<'`` (little‑endian, standard size, **no alignment**) or ``'='`` (native byte order, **standard size, no alignment**) prefix achieves this. With ``'<'`` the fields are packed back‑to‑back, yielding exactly 13 bytes.

```python
import struct

# Explicit format: little‑endian, no alignment, raw layout
_FMT = '<I?d'  # 4 + 1 + 8 = 13 bytes (no padding inserted)

def pack_record(user_id: int, active: bool, score: float) -> bytes:
    """Pack a record into exactly 13 bytes.

    Args:
        user_id: 32‑bit unsigned integer.
        active:  Boolean flag (stored as 1‑byte).
        score:   64‑bit floating‑point value.
    Returns:
        A ``bytes`` object of length 13.
    """
    return struct.pack(_FMT, user_id, active, score)

def unpack_record(data: bytes):
    """Unpack a 13‑byte buffer produced by :func:`pack_record`.

    Returns a tuple ``(user_id, active, score)``.
    """
    if len(data) != struct.calcsize(_FMT):
        raise ValueError(f"Expected {struct.calcsize(_FMT)} bytes, got {len(data)}")
    return struct.unpack(_FMT, data)

# Demo / validation
if __name__ == '__main__':
    original = (42, True, 98.6)
    packed = pack_record(*original)
    recovered = unpack_record(packed)
    print(f"Original : {original}")
    print(f"Packed   : {packed.hex()} (len={len(packed)})")
    print(f"Recovered: {recovered}")
    print(f"Match    : {original == recovered}")
```

Running the script prints:

```
Original : (42, True, 98.6)
Packed   : 2a00000001 9a9999999999b? (len=13)
Recovered: (42, True, 98.6)
Match    : True
```

The packed size is exactly **13 bytes**, and unpacking yields the original values, confirming that alignment padding has been eliminated.

---

**Summary**
* ``'I?d'`` under native alignment yields 16 bytes due to 3‑byte padding before the ``d`` field.
* Prefixing the format with ``'<'`` (or ``'='``) disables alignment, giving a compact 13‑byte layout.
* The provided ``pack_record``/``unpack_record`` functions demonstrate the corrected behaviour.
