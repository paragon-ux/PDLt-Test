def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _strict_vertices(pts):
    """Classic Jarvis march, counter-clockwise: from each vertex the next one has no
    point to its right; a collinear tie goes to the farthest point."""
    start = pts[0]
    hull, current = [], start
    while True:
        hull.append(current)
        candidate = pts[1] if current == pts[0] else pts[0]
        for p in pts:
            if p == current:
                continue
            turn = _cross(current, candidate, p)
            if turn < 0 or (turn == 0 and _dist2(current, p) > _dist2(current, candidate)):
                candidate = p
        current = candidate
        if current == start:
            return hull


def convex_hull(points):
    """Gift wrapping, counter-clockwise, with every point on the hull boundary."""
    pts = sorted(set(map(tuple, points)))
    if len(pts) <= 2:
        return pts
    if all(_cross(pts[0], pts[-1], p) == 0 for p in pts):
        return pts  # degenerate: the boundary is the segment itself
    vertices = _strict_vertices(pts)
    hull = []
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        hull.append(a)
        between = [p for p in pts if p not in (a, b) and _cross(a, b, p) == 0
                   and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
                   and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])]
        hull.extend(sorted(between, key=lambda p: _dist2(a, p)))
    return hull
