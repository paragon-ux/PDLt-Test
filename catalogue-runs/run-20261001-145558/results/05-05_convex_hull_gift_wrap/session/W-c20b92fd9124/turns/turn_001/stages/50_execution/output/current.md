import sys
from typing import List, Tuple

def jarvis_march(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Return the convex hull of a set of 2D points using the Jarvis March algorithm.
    All points on the hull boundary (including collinear points) are returned in
    counter‑clockwise order. Duplicate points are ignored.
    """
    # Remove duplicate points
    points = list(set(points))
    if len(points) < 3:
        # All points are hull themselves (including collinear degenerate case)
        # Return sorted unique points counter‑clockwise (just sorted by angle from centroid)
        return points

    # Helper functions
    def orientation(p: Tuple[float, float], q: Tuple[float, float], r: Tuple[float, float]) -> float:
        # >0 if counter‑clockwise, <0 if clockwise, 0 if collinear
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def distance_sq(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    # Find the leftmost (and lowest) point
    start = min(points, key=lambda p: (p[0], p[1]))
    hull: List[Tuple[float, float]] = []
    point_on_hull = start
    while True:
        hull.append(point_on_hull)
        # Choose an initial candidate different from point_on_hull
        candidate = None
        for p in points:
            if p == point_on_hull:
                continue
            candidate = p
            break
        if candidate is None:
            break  # all points are identical
        # Scan all points to find the most counter‑clockwise relative to point_on_hull
        for p in points:
            if p == point_on_hull or p == candidate:
                continue
            orient = orientation(point_on_hull, candidate, p)
            if orient < 0:
                # p is more counter‑clockwise than candidate
                candidate = p
            elif orient == 0:
                # Collinear: keep the farthest one as candidate
                if distance_sq(point_on_hull, p) > distance_sq(point_on_hull, candidate):
                    candidate = p
        # After selecting candidate, include all collinear points on the edge
        edge_points = []
        for p in points:
            if p == point_on_hull or p == candidate:
                continue
            if orientation(point_on_hull, candidate, p) == 0:
                # Collinear with the edge; check if it lies between the endpoints
                if (min(point_on_hull[0], candidate[0]) <= p[0] <= max(point_on_hull[0], candidate[0]) and
                    min(point_on_hull[1], candidate[1]) <= p[1] <= max(point_on_hull[1], candidate[1])):
                    edge_points.append(p)
        # Sort collinear points along the edge from point_on_hull towards candidate
        edge_points.sort(key=lambda pt: distance_sq(point_on_hull, pt))
        # Insert them after the current point_on_hull
        for ep in edge_points:
            hull.append(ep)
        # Move to next point
        if candidate == start:
            break
        point_on_hull = candidate
    # Ensure counter‑clockwise order (Jarvis already produces it)
    return hull

# Simple test harness
if __name__ == "__main__":
    test_cases = [
        # Simple convex polygon (square)
        [(0,0), (0,1), (1,1), (1,0)],
        # Polygon with collinear edge points
        [(0,0), (1,0), (2,0), (2,2), (0,2)],
        # All points collinear
        [(0,0), (1,1), (2,2), (3,3)],
        # Duplicate points
        [(0,0), (1,1), (0,0), (1,1), (2,0)]
    ]
    for i, pts in enumerate(test_cases, 1):
        hull = jarvis_march(pts)
        print(f"Test case {i}: hull = {hull}")
