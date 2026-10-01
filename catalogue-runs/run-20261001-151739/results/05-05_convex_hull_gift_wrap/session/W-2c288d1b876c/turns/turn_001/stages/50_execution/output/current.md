def jarvis_march(points):
    """Compute the convex hull of a set of 2D points using the Gift Wrapping (Jarvis March) algorithm.
    Includes all collinear points on the hull boundary.
    Returns the hull vertices in counter‑clockwise order.
    """
    # Remove duplicate points
    points = list(set(points))
    n = len(points)
    if n == 0:
        return []
    if n == 1:
        return points
    # Find the leftmost (and bottommost) point
    start = min(points, key=lambda p: (p[0], p[1]))
    hull = []
    point_on_hull = start
    while True:
        hull.append(point_on_hull)
        # Choose a candidate for next point
        endpoint = points[0]
        for p in points[1:]:
            if endpoint == point_on_hull:
                endpoint = p
                continue
            # Compute orientation
            cross = ((endpoint[0] - point_on_hull[0]) * (p[1] - point_on_hull[1]) -
                     (endpoint[1] - point_on_hull[1]) * (p[0] - point_on_hull[0]))
            if cross < 0:
                endpoint = p
            elif cross == 0:
                # Collinear: keep the farthest point
                if (p[0] - point_on_hull[0])**2 + (p[1] - point_on_hull[1])**2 > \
                   (endpoint[0] - point_on_hull[0])**2 + (endpoint[1] - point_on_hull[1])**2:
                    endpoint = p
        # Add all points collinear with point_on_hull and endpoint that lie between them
        collinear_points = []
        for p in points:
            if p == point_on_hull or p == endpoint:
                continue
            cross = ((endpoint[0] - point_on_hull[0]) * (p[1] - point_on_hull[1]) -
                     (endpoint[1] - point_on_hull[1]) * (p[0] - point_on_hull[0]))
            if cross == 0:
                # Check if p is between point_on_hull and endpoint
                dot = ((p[0] - point_on_hull[0]) * (endpoint[0] - point_on_hull[0]) +
                       (p[1] - point_on_hull[1]) * (endpoint[1] - point_on_hull[1]))
                if 0 < dot < ((endpoint[0] - point_on_hull[0])**2 + (endpoint[1] - point_on_hull[1])**2):
                    collinear_points.append(p)
        # Sort collinear points by distance from point_on_hull to maintain order
        collinear_points.sort(key=lambda p: ((p[0] - point_on_hull[0])**2 + (p[1] - point_on_hull[1])**2))
        for cp in collinear_points:
            hull.append(cp)
        # Move to next point
        point_on_hull = endpoint
        if point_on_hull == start:
            break
    # Remove possible duplicates while preserving order
    unique_hull = []
    for p in hull:
        if p not in unique_hull:
            unique_hull.append(p)
    return unique_hull

# Test cases
if __name__ == "__main__":
    # Simple convex polygon (square)
    points1 = [(0, 0), (0, 1), (1, 1), (1, 0)]
    print("Hull 1:", jarvis_march(points1))

    # Points with collinear edges (rectangle with extra points on edges)
    points2 = [(0, 0), (0, 2), (0, 1), (2, 0), (2, 2), (1, 0), (1, 2)]
    print("Hull 2:", jarvis_march(points2))

    # All points collinear (degenerate case)
    points3 = [(0, 0), (1, 0), (2, 0), (3, 0)]
    print("Hull 3:", jarvis_march(points3))

    # Duplicate points
    points4 = [(0, 0), (1, 1), (0, 0), (1, 1), (2, 0), (2, 0)]
    print("Hull 4:", jarvis_march(points4))
