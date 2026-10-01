READ the input list of (x, y) points
REMOVE duplicate points
IDENTIFY the leftmost (and lowest) point as start
INITIALIZE hull with the start point
FOR each hull vertex DO
    SELECT the candidate point that yields the smallest polar angle relative to the current edge
    IF multiple points are collinear with the current edge THEN
        INCLUDE all collinear points in order along the edge
    ENDIF
    APPEND the selected point(s) to the hull
    CONTINUE until the start point is reached again
ENDFOR
OUTPUT the hull vertices in counter‑clockwise order
TEST the implementation with a simple convex polygon
TEST with points that have collinear edges
TEST with all points collinear (degenerate case)
TEST with duplicate points
