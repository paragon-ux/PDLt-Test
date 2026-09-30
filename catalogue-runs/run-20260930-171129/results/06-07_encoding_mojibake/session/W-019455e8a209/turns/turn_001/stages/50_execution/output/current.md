# encoding_fix.py
"""Corrected save and load functions with UTF-8 handling and a round‑trip test.
The file also contains a demonstration of the original mojibake problem for reference.
"""

def save_to_file(text: str, filepath: str) -> None:
    """Save *text* to *filepath* using UTF‑8 encoding.
    This replaces the previous Latin‑1 implementation which corrupted any
    character outside the ISO‑8859‑1 range.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)


def load_from_file(filepath: str) -> str:
    """Load text from *filepath* assuming UTF‑8 encoding.
    The original loader used UTF‑8 on a file written as Latin‑1, causing
    decode errors or mojibake.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# --- Original (broken) implementation for illustration ---

def _broken_save_to_file(text: str, filepath: str) -> None:
    with open(filepath, "w", encoding="latin-1") as f:
        f.write(text)

def _broken_load_from_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# --- Test ----------------------------------------------------------
if __name__ == "__main__":
    # String containing characters from three Unicode blocks:
    #   Latin (accented) → "é", "ñ", "Ü"
    #   CJK (Han)       → "漢", "字"
    #   Emoji           → "😀", "🚀"
    test_string = "Café résumé naïve Ü漢字 😀🚀"
    path = "test_data.txt"

    # Write and read using the corrected functions
    save_to_file(test_string, path)
    recovered = load_from_file(path)

    print("Original :", test_string)
    print("Recovered:", recovered)
    print("Match    :", test_string == recovered)

    # Demonstrate the broken round‑trip (for diagnostic purposes)
    _broken_save_to_file(test_string, path)
    broken = _broken_load_from_file(path)
    print("\n--- Broken round‑trip ---")
    print("Recovered (broken):", broken)
    print("Match (broken)    :", test_string == broken)
