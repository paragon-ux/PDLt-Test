```python
from typing import List, Tuple

def orientation(p: Tuple[float, float], q: Tuple[float, float], r: Tuple[float, float]) -> int:
    """Return 0 if collinear, 1 if clockwise, 2 if counterclockwise."""
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if abs(val) < 1e-12:
        return 0
    return 1 if val > 0 else 2

def jarvis_march(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Gift wrapping algorithm that includes collinear points on edges.
    Returns convex hull vertices in counter‑clockwise order.
    """
    # Remove duplicates
    unique = list(dict.fromkeys(points))
    n = len(unique)
    if n == 0:
        return []
    if n == 1:
        return unique
    # Find leftmost point (lowest y as tie‑breaker)
    start = min(unique, key=lambda p: (p[0], p[1]))
    hull = []
    point_on_hull = start
    while True:
        hull.append(point_on_hull)
        # Choose a candidate different from point_on_hull
        candidate = None
        for pt in unique:
            if pt == point_on_hull:
                continue
            candidate = pt
            break
        # Find the most counter‑clockwise point relative to point_on_hull
        for pt in unique:
            if pt == point_on_hull or pt == candidate:
                continue
            o = orientation(point_on_hull, candidate, pt)
            if o == 2:  # pt is more counter‑clockwise
                candidate = pt
            elif o == 0:
                # Collinear: keep the farthest point to include all boundary points later
                if (pt[0] - point_on_hull[0])**2 + (pt[1] - point_on_hull[1])**2 > \
                   (candidate[0] - point_on_hull[0])**2 + (candidate[1] - point_on_hull[1])**2:
                    candidate = pt
        # After selecting candidate, add any intermediate collinear points on the edge
        edge_points = []
        for pt in unique:
            if pt == point_on_hull or pt == candidate:
                continue
            if orientation(point_on_hull, candidate, pt) == 0:
                # Check if pt lies between point_on_hull and candidate
                if min(point_on_hull[0], candidate[0]) <= pt[0] <= max(point_on_hull[0], candidate[0]) and \
                   min(point_on_hull[1], candidate[1]) <= pt[1] <= max(point_on_hull[1], candidate[1]):
                    edge_points.append(pt)
        # Sort edge points along the edge direction
        if edge_points:
            edge_points.sort(key=lambda p: (p[0] - point_on_hull[0])**2 + (p[1] - point_on_hull[1])**2)
            for p in edge_points:
                if p not in hull:
                    hull.append(p)
        # Move to next point
        point_on_hull = candidate
        if point_on_hull == start:
            break
    # Ensure counter‑clockwise order (already guaranteed) and remove possible duplicates
    # Final pass to keep unique while preserving order
    final_hull = []
    for p in hull:
        if not final_hull or final_hull[-1] != p:
            final_hull.append(p)
    return final_hull

# ---------- Test Suite ----------
import unittest

class TestJarvisMarch(unittest.TestCase):
    def test_simple_convex_polygon(self):
        pts = [(0,0), (2,0), (2,2), (0,2), (1,1)]
        hull = jarvis_march(pts)
        expected = [(0,0), (2,0), (2,2), (0,2)]
        self.assertCountEqual(hull, expected)

    def test_collinear_edges(self):
        pts = [(0,0), (1,0), (2,0), (2,2), (1,2), (0,2)]
        hull = jarvis_march(pts)
        expected = [(0,0), (2,0), (2,2), (0,2)]
        self.assertCountEqual(hull, expected)
        # Ensure collinear points on edges are present
        self.assertIn((1,0), hull)
        self.assertIn((1,2), hull)

    def test_all_collinear(self):
        pts = [(0,0), (1,1), (2,2), (3,3)]
        hull = jarvis_march(pts)
        # All points should be returned in order
        self.assertCountEqual(hull, pts)

    def test_duplicate_points(self):
        pts = [(0,0), (1,1), (0,0), (2,0), (2,0), (1,1)]
        hull = jarvis_march(pts)
        expected = [(0,0), (2,0), (1,1)]
        self.assertCountEqual(hull, expected)

if __name__ == "__main__":
    unittest.main()
```
