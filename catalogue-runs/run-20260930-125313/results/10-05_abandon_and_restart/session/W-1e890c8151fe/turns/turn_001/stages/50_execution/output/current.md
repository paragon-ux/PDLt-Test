# caesar_cipher.py
"""Caesar cipher encoder and decoder.
Implements the requirements from the confirmed prompt.
"""

def caesar_shift_char(c: str, shift: int, encode: bool = True) -> str:
    if not c.isalpha():
        return c
    base = ord('A') if c.isupper() else ord('a')
    offset = ord(c) - base
    if not encode:
        shift = -shift
    shifted = (offset + shift) % 26
    return chr(base + shifted)

def caesar_cipher(text: str, shift: int, operation: str) -> str:
    encode = operation.lower() == 'encode'
    return ''.join(caesar_shift_char(ch, shift, encode) for ch in text)

if __name__ == "__main__":
    import sys
    # Expect three lines on stdin: operation, shift, text
    operation = sys.stdin.readline().strip()
    shift_line = sys.stdin.readline().strip()
    try:
        shift = int(shift_line)
    except ValueError:
        print("Invalid shift value", file=sys.stderr)
        sys.exit(1)
    text = sys.stdin.read()
    result = caesar_cipher(text, shift, operation)
    print(result)
