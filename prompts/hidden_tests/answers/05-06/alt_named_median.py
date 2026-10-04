# Correct with a different name; partitions the shorter array by binary search.
def median(xs, ys):
    if len(xs) > len(ys):
        xs, ys = ys, xs
    total = len(xs) + len(ys)
    lo, hi = 0, len(xs)
    while True:
        cut_x = (lo + hi) // 2
        cut_y = (total + 1) // 2 - cut_x
        lx = xs[cut_x - 1] if cut_x else -10**18
        rx = xs[cut_x] if cut_x < len(xs) else 10**18
        ly = ys[cut_y - 1] if cut_y else -10**18
        ry = ys[cut_y] if cut_y < len(ys) else 10**18
        if lx <= ry and ly <= rx:
            return max(lx, ly) * 1.0 if total % 2 else (max(lx, ly) + min(rx, ry)) / 2.0
        if lx > ry:
            hi = cut_x - 1
        else:
            lo = cut_x + 1
