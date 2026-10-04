```python
import re

EMAIL = re.compile(r"^(?P<user>[A-Za-z0-9._%-]+)(?:\+(?P<tag>[A-Za-z0-9._%-]+))?@(?P<domain>[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)$")

def validate_email(address: str) -> dict:
    m = EMAIL.match(address)
    if not m:
        return {"valid": False, "local_part": None, "domain": None, "tag": None}
    local = m.group("user") + (f"+{m.group('tag')}" if m.group("tag") else "")
    return {"valid": True, "local_part": local, "domain": m.group("domain"), "tag": m.group("tag")}

assert validate_email("user+news@example.com") == {"valid": True, "local_part": "user+news", "domain": "example.com", "tag": "news"}
assert validate_email("user@example.com")["tag"] is None
assert not validate_email("user@localhost")["valid"]
```
