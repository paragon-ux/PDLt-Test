# Correct output with a different algorithm and name: Andrew's monotone chain keeping
# collinear points (the hull points are the same set, in the same counter-clockwise order).
def gift_wrap(points):
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    pts = sorted(set(tuple(p) for p in points))
    if len(pts) < 3:
        return pts
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) < 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) < 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    seen, out = set(), []
    for p in hull:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out
