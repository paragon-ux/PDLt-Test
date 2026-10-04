# Correct with a different interface: a differently named function returning tuples.
def merge_insert(existing, new):
    merged = []
    start, end = new
    added = False
    for s, e in existing:
        if e < start:
            merged.append((s, e))
        elif s > end:
            if not added:
                merged.append((start, end))
                added = True
            merged.append((s, e))
        else:
            start, end = min(start, s), max(end, e)
    if not added:
        merged.append((start, end))
    return merged
