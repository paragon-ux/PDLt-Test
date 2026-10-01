def save_to_file(text, filepath):
    """Save text to a file using UTF-8 encoding.
    This preserves all Unicode characters.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

def load_from_file(filepath):
    """Load text from a file using UTF-8 encoding.
    This matches the encoding used by save_to_file.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# Test script
if __name__ == "__main__":
    import tempfile, os
    # String containing characters from Latin, CJK, and Emoji blocks
    test_string = (
        "Café résumé naïve Üntermensch "  # Latin (including accented characters)
        "汉字漢字"                       # CJK (Chinese characters)
        " 😃🚀🌟"                         # Emoji
    )
    # Use a temporary file for the round‑trip test
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
        temp_path = tmp.name
    try:
        save_to_file(test_string, temp_path)
        recovered = load_from_file(temp_path)
        assert test_string == recovered, "Round‑trip mismatch"
        print("Test passed: recovered string matches original.")
    finally:
        os.remove(temp_path)
