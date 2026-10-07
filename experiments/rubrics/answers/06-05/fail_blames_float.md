The values read back wrong because 98.6 can't be represented exactly as a float, so the recovered score differs slightly. The size is 16 because Python stores booleans as 4-byte ints.

Fix: round the score when unpacking:
```python
def unpack_record(data):
    user_id, active, score = struct.unpack('I?d', data)
    return user_id, active, round(score, 2)
```
