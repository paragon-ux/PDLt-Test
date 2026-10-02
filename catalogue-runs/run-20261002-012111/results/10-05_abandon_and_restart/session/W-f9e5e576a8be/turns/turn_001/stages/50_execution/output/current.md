def caesar_encode(text: str, shift: int) -> str:
    """Encode a string using a Caesar cipher.

    Args:
        text: The input string to encode.
        shift: The number of positions to shift each alphabetic character.

    Returns:
        The encoded string with alphabetic characters shifted by *shift*.
    """
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            # Perform shift with wrap-around using modulo 26
            shifted = (ord(ch) - base + shift) % 26 + base
            result.append(chr(shifted))
        else:
            # Non‑alphabetic characters are left unchanged
            result.append(ch)
    return ''.join(result)

def caesar_decode(text: str, shift: int) -> str:
    """Decode a Caesar‑cipher encoded string.

    Args:
        text: The encoded string to decode.
        shift: The shift value that was used for encoding.

    Returns:
        The original decoded string.
    """
    # Decoding is the inverse operation: shift backwards
    return caesar_encode(text, -shift)
