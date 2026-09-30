# Caesar cipher encoder and decoder implementation

def caesar_encode(text: str, shift: int) -> str:
    """Encode *text* by shifting alphabetic characters forward by *shift* positions.
    Non‑alphabetic characters are left unchanged. Case is preserved.
    """
    result = []
    for ch in text:
        if 'a' <= ch <= 'z':
            # lower‑case shift with wrap‑around
            offset = (ord(ch) - ord('a') + shift) % 26
            result.append(chr(ord('a') + offset))
        elif 'A' <= ch <= 'Z':
            # upper‑case shift with wrap‑around
            offset = (ord(ch) - ord('A') + shift) % 26
            result.append(chr(ord('A') + offset))
        else:
            result.append(ch)
    return ''.join(result)

def caesar_decode(text: str, shift: int) -> str:
    """Decode *text* that was encoded with a Caesar cipher of *shift*.
    The operation shifts alphabetic characters backward, preserving case and
    leaving non‑alphabetic characters unchanged.
    """
    return caesar_encode(text, -shift)

# The module provides two functions: caesar_encode and caesar_decode.
# No executable code or example usage is included as per the specification.
