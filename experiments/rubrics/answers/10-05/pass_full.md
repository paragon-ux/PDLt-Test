```python
import string

_ROT13 = str.maketrans(string.ascii_lowercase + string.ascii_uppercase,
                       string.ascii_lowercase[13:] + string.ascii_lowercase[:13] +
                       string.ascii_uppercase[13:] + string.ascii_uppercase[:13])

def rot13(text: str) -> str:
    return text.translate(_ROT13)

assert rot13("Hello, World!") == "Uryyb, Jbeyq!"
```
Applying it twice returns the original text.
