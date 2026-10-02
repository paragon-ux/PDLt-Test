import sys
from typing import List, Tuple

def orientation(p: Tuple[float, float], q: Tuple[float, float], r: Tuple[float, float]) -> float:
    """Cross product of vectors pq x pr. Positive for counter‑clockwise turn, negative for clockwise, zero for collinear."""
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

def jarvis_march(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Gift wrapping algorithm that returns the convex hull in counter‑clockwise order,
    including all collinear points on the hull boundary.
    """
    if not points:
        raise ValueError("Input point list must be non‑empty")
    # Remove duplicates
    uniq = list(dict.fromkeys(points))
    if len(uniq) < 3:
        # All points (0, 1 or 2) are trivially the hull
        return uniq
    # Find left‑most (and bottom‑most on tie) point
    start = min(uniq, key=lambda p: (p[0], p[1]))
    hull = []
    current = start
    while True:
        hull.append(current)
        # Choose a candidate different from current
        candidate = None
        for pt in uniq:
            if pt == current:
                continue
            candidate = pt
            break
        for pt in uniq:
            if pt == current or pt == candidate:
                continue
            orient = orientation(current, candidate, pt)
            if orient < 0:
                # pt is more counter‑clockwise than candidate
                candidate = pt
            elif orient == 0:
                # Collinear: keep the farthest point to include all boundary points later
                # Compare distances
                if (pt[0] - current[0])**2 + (pt[1] - current[1])**2 > (candidate[0] - current[0])**2 + (candidate[1] - current[1])**2:
                    candidate = pt
        # After scanning, candidate is the next hull point
        # To include intermediate collinear points, walk from current to candidate and collect them
        if candidate == start:
            # Add any remaining collinear points on the last edge before closing
            # Find points collinear with current->start and farther than current
            collinear_pts = []
            for pt in uniq:
                if pt in (current, start):
                    continue
                if orientation(current, start, pt) == 0:
                    # Check if pt lies between current and start (inclusive)
                    collinear_pts.append(pt)
            # Sort collinear points by distance from current
            collinear_pts.sort(key=lambda p: ((p[0] - current[0])**2 + (p[1] - current[1])**2))
            hull.extend(collinear_pts)
            break
        # Insert collinear points on edge current->candidate (excluding endpoints)
        edge_pts = []
        for pt in uniq:
            if pt in (current, candidate):
                continue
            if orientation(current, candidate, pt) == 0:
                # Check if pt lies between current and candidate
                if ((pt[0] - current[0]) * (pt[0] - candidate[0]) <= 0) and ((pt[1] - current[1]) * (pt[1] - candidate[1]) <= 0):
                    edge_pts.append(pt)
        # Sort by distance from current to preserve order
        edge_pts.sort(key=lambda p: ((p[0] - current[0])**2 + (p[1] - current[1])**2))
        hull.extend(edge_pts)
        current = candidate
        if current == start:
            break
    # Remove possible duplicates while preserving order
    seen = set()
    final_hull = []
    for pt in hull:
        if pt not in seen:
            final_hull.append(pt)
            seen.add(pt)
    return final_hull

# ---------- Test Cases ----------
if __name__ == "__main__":
    def test(name, pts, expected):
        result = jarvis_march(pts)
        print(name, "->", result)
        assert result == expected, f"{name} failed"

    # Simple convex polygon (square)
    test(
        "Square",
        [(0,0), (0,1), (1,1), (1,0)],
        [(0, 0), (1, 0), (1, 1), (0, 1)]
    )

    # Polygon with collinear edge points
    test(
        "Collinear Edge",
        [(0,0), (2,0), (1,0), (2,2), (0,2)],
        [(0, 0), (2, 0), (2, 2), (0, 2)]
    )

    # All points collinear
    test(
        "All Collinear",
        [(0,0), (1,0), (2,0), (3,0)],
        [(0, 0), (1, 0), (2, 0), (3, 0)]
    )

    # Duplicate points
    test(
        "Duplicates",
        [(0,0), (1,1), (0,0), (1,1), (0,1), (1,0)],
        [(0, 0), (1, 0), (1, 1), (0, 1)]
    )
