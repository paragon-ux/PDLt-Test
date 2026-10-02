VALIDATE the input list of 2D points is non-empty.
REMOVE duplicate points from the input.
IF the number of unique points is less than 3 THEN
    RETURN the unique points as the convex hull.
ENDIF
SELECT the point with the smallest x-coordinate (and smallest y if tie) as the start vertex.
INITIALIZE an empty list to hold hull vertices.
SET current vertex to the start vertex.
REPEAT
    ADD current vertex to the hull list.
    SELECT the next vertex by scanning all other points and choosing the one that yields the most counter‑clockwise orientation relative to the current vertex, INCLUDING collinear points on the hull boundary.
    IF the selected next vertex equals the start vertex THEN
        EXIT REPEAT.
    ENDIF
    SET current vertex to the selected next vertex.
ENDREPEAT
ENSURE the hull vertices are ordered counter‑clockwise and include all collinear boundary points.
RETURN the hull vertices.

DEFINE a test case for a simple convex polygon.
DEFINE a test case for points with collinear edges on the hull.
DEFINE a test case for the degenerate case where all points are collinear.
DEFINE a test case that includes duplicate points.
FOR each test case DO
    INVOKE the convex hull implementation with the test case points.
    VERIFY that the output hull matches the expected counter‑clockwise ordering and includes collinear points where required.
ENDFOR
