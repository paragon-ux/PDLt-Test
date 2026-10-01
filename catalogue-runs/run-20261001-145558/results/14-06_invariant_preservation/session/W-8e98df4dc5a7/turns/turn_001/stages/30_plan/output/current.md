BASE CASE:
  VERIFY the invariant holds with no transitions (both directions start RED, at most one direction non-RED)
INDUCTIVE STEP:
  ASSUME the invariant holds after k transitions of the combined system
  FOR each possible transition (RED→GREEN after 60 s, GREEN→YELLOW after 45 s, YELLOW→RED after 5 s):
    APPLY the transition rule
    ENSURE direction B may transition to GREEN only when direction A is RED
    VERIFY the invariant remains true after the transition
  CONCLUDE the invariant holds after the (k+1)‑th transition
