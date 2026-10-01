# Caesar cipher encoder and decoder

def caesar_encode(text: str, shift: int) -> str:
    """Encode *text* by shifting each alphabetic character forward by *shift*.
    Non‑alphabetic characters are left unchanged. Case is preserved.
    """
    result = []
    for ch in text:
        if 'a' <= ch <= 'z':
            offset = ord('a')
            result.append(chr((ord(ch) - offset + shift) % 26 + offset))
        elif 'A' <= ch <= 'Z':
            offset = ord('A')
            result.append(chr((ord(ch) - offset + shift) % 26 + offset))
        else:
            result.append(ch)
    return ''.join(result)

def caesar_decode(text: str, shift: int) -> str:
    """Decode *text* that was encoded with a Caesar cipher using *shift*.
    This simply shifts characters in the opposite direction.
    """
    return caesar_encode(text, -shift)

# Example usage demonstrating the Caesar cipher encoder and decoder
if __name__ == "__main__":
    sample = "Hello, World!"
    offset = 3
    encoded = caesar_encode(sample, offset)
    decoded = caesar_decode(encoded, offset)
    print(f"Original: {sample}")
    print(f"Encoded : {encoded}")
    print(f"Decoded : {decoded}")
