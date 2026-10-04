Struct inserts padding for alignment, so the packed record is 16 bytes rather than 13 (the double is aligned to 8 bytes). To fix it, just compute the size with struct.calcsize and use that instead of assuming 13:

```python
size = struct.calcsize('I?d')
print(f"Packed size: {len(packed)} bytes (expected: {size})")
```
Now the size check matches.
