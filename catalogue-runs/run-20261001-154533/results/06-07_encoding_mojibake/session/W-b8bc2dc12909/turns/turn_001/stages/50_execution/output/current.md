```python
import os
import tempfile

def save_to_file(text: str, filepath: str) -> None:
    """Save text to a file using UTF-8 encoding.

    UTF-8 is a Unicode‑preserving, widely‑supported encoding that can represent
    any character in the Unicode repertoire. Using the same encoding for both
    saving and loading prevents round‑trip corruption.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

def load_from_file(filepath: str) -> str:
    """Load text from a file that was saved with UTF-8 encoding.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def test_utf8_roundtrip() -> None:
    """Write and read a string containing characters from Latin, CJK, and Emoji.
    The test verifies that the recovered string exactly matches the original.
    """
    test_string = (
        "Café résumé naïve Üntermensch, 你好世界, 😊🚀"
    )
    # Use a temporary file to avoid side effects.
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test.txt")
        # Write using the corrected save function.
        save_to_file(test_string, file_path)
        # Read using the corrected load function.
        recovered = load_from_file(file_path)
        assert recovered == test_string, (
            f"Round‑trip failed.\nOriginal: {test_string}\nRecovered: {recovered}"
        )
        print("Round‑trip successful. Recovered string matches the original.")

if __name__ == "__main__":
    test_utf8_roundtrip()
```
