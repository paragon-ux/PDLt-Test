```python
def caesar_encode(text, shift):
    out = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)

def caesar_decode(text, shift):
    return caesar_encode(text, -shift)

def rot13(text):
    return caesar_encode(text, 13)
```
The Caesar encoder and decoder from before, with ROT13 as a special case.
