IDENTIFY required assumptions about the controller logic (e.g., mutually exclusive green phases, atomic state updates)
FOR EACH possible transition of the traffic‑light controller state machines
VERIFY that if at most one direction has a non‑RED light before the transition, then after the transition at most one direction has a non‑RED light
IF all transitions are verified
INFER by induction on the number of transitions that the invariant "at most one direction has a non‑RED light at any time" holds for all reachable states
