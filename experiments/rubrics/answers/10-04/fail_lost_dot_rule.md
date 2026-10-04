```python
import re

def validate_email(address):
    m = re.match(r"^([\w.]+)(?:\+(\w+))?@([\w.-]+)$", address)
    if not m:
        return {"valid": False, "local_part": None, "domain": None, "tag": None}
    return {"valid": True, "local_part": m.group(1), "domain": m.group(3), "tag": m.group(2)}
```
`user@localhost` is accepted as a local-network address.
