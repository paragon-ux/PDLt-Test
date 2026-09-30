BASE CASE: Assume the invariant holds before any transitions.
INDUCTIVE STEP: FOR each possible transition of the traffic light controller state machines, SHOW that if at most one direction has a non-RED light before the transition, then after the transition at most one direction has a non-RED light.
IDENTIFY ASSUMPTIONS: LIST any required assumptions about the controller logic (e.g., mutually exclusive green phases, atomic state updates) needed for the invariant to be preserved.
CONCLUDE: STATE that by induction on the number of transitions, the invariant "At most one direction has a non-RED light at any time" holds for all reachable states.
