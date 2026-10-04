# Wrong: merges overlaps but appends a non-overlapping new interval at the end.
def insert_interval(intervals, new_interval):
    lo, hi = new_interval
    out = []
    for a, b in intervals:
        if b < lo or a > hi:
            out.append([a, b])
        else:
            lo, hi = min(lo, a), max(hi, b)
    out.append([lo, hi])
    return out
