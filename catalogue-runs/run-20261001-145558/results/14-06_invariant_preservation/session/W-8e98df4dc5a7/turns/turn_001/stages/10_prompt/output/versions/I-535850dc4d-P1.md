BASE CASE: Verify the invariant when no transitions have occurred; both directions start with RED, so at most one direction has a non-RED light.
INDUCTIVE STEP: ASSUME the invariant holds after k transitions of the combined system of direction A and direction B.
SHOW that after the (k+1)‑th transition the invariant still holds.
- Consider each possible transition: RED→GREEN after 60 seconds, GREEN→YELLOW after 45 seconds, YELLOW→RED after 5 seconds.
- Use the rule that direction B may transition to GREEN only when direction A is in RED.
- Identify any necessary assumptions (e.g., timing synchronisation, exclusive control of the shared intersection).
