# Fixed encoding functions using UTF-8 (a Unicode‑compatible encoding)

def save_to_file(text: str, filepath: str) -> None:
    """Save *text* to *filepath* using UTF‑8 encoding.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)


def load_from_file(filepath: str) -> str:
    """Load text from *filepath* assuming UTF‑8 encoding.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# Test script demonstrating the fix
if __name__ == "__main__":
    # Sample text containing characters from three Unicode blocks:
    #   • Latin‑1 Supplement (diacritics)
    #   • CJK Unified Ideographs (Chinese characters)
    #   • Emoji (Emoticons)
    sample_text = (
        "Café résumé naïve Üntermensch "  # Latin‑1 Supplement
        "中文例子 "                         # CJK
        "🚀🔥😊"                             # Emoji
    )

    file_path = "test_data.txt"
    save_to_file(sample_text, file_path)
    recovered = load_from_file(file_path)

    print("Original:  ", sample_text)
    print("Recovered: ", recovered)
    print("Match: ", sample_text == recovered)
    # Assertion to ensure exact round‑trip fidelity
    assert sample_text == recovered, "Round‑trip mismatch!"
