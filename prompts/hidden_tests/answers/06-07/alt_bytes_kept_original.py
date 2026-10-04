# Correct with a different interface: originals kept; the fixed pair works on bytes
# with an explicit UTF-8 codec and newline-preserving I/O.
def save_to_file(text, filepath):
    with open(filepath, 'w', encoding='latin-1') as f:
        f.write(text)


def load_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def save_text_utf8(text, path):
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))


def load_text_utf8(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")
