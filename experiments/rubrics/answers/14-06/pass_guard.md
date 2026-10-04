Invariant I: A = RED or B = RED (at most one direction is non-RED).

Assumptions needed: (1) transitions are atomic and occur one at a time; (2) the stated rule guards B: B goes RED -> GREEN only when A is RED (entering RED); (3) a symmetric guard for A is required: A goes RED -> GREEN only when B is RED. The prompt states only (2); without (3), A could turn GREEN while B is GREEN, so the controller must enforce mutual exclusion in both directions.

Base case: B starts RED, so I holds whatever A's state is.

Inductive step: assume I holds after k transitions; consider transition k+1 of direction X (the other is Y).
- X -> RED (from YELLOW): afterwards X = RED, so I holds.
- X: GREEN -> YELLOW: before, X was non-RED, so by I, Y = RED; after, Y is still RED. I holds.
- X: RED -> GREEN: by the guard (2) or (3), Y is RED at that moment, and Y does not change in this step; I holds.
So every transition preserves I, and by induction I holds after any number of transitions.
