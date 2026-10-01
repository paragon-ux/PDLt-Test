PARSE the supplied list of 45 distinct positive integers
GENERATE all candidate triples (a, b, c) such that a + b = c, all three numbers are in the list, and a, b, c are distinct
INDEX each integer to the candidate triples that contain it
APPLY an exact‑cover search (e.g., recursive backtracking or Algorithm X) to select 15 disjoint triples that together use every integer exactly once
IF a complete cover is found THEN FORMAT the selected triples as a list of (a, b, c) entries
ELSE INDICATE that no such partition exists
