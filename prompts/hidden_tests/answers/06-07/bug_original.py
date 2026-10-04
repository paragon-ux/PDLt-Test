# Wrong: the original latin-1 write / utf-8 read mismatch.
def save_to_file(text, filepath):
    with open(filepath, 'w', encoding='latin-1') as f:
        f.write(text)


def load_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()
