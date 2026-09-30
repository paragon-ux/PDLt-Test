BASE CASE: VERIFY that the invariant "At most one direction has a non-RED light at any time" holds in the initial configuration of the traffic‑light controller.
INDUCTIVE STEP: ASSUME the invariant holds after k transitions of the controller state machines.
FOR EACH possible transition from the k‑th state, SHOW that the resulting state also satisfies the invariant.
IDENTIFY any necessary assumptions about the controller logic (e.g., mutually exclusive green phases, exclusive assignment of non‑RED colors) that must be true for the proof to remain valid.
CONCLUDE that, by mathematical induction, the invariant is preserved for any number of transitions.
