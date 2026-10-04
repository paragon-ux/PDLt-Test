# Wrong: "fixes" the crash by replacing what latin-1 cannot encode.
def save_to_file(text, filepath):
    with open(filepath, 'w', encoding='latin-1', errors='replace') as f:
        f.write(text)


def load_from_file(filepath):
    with open(filepath, 'r', encoding='latin-1') as f:
        return f.read()
