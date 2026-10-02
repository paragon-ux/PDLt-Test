**Proof Outline**

**Invariant:** At most one direction has a non-RED light at any time.

**State Machine Description**
- Each direction (A and B) runs its own traffic‑light controller with states {RED, GREEN, YELLOW}.
- Transitions for a single controller:
  * RED → GREEN after 60 s
  * GREEN → YELLOW after 45 s
  * YELLOW → RED after 5 s
- Direction B is allowed to transition to GREEN only when direction A is in RED (i.e., the two controllers are coordinated so that both directions are never GREEN simultaneously).

**Assumptions**
1. The two directions are perfectly synchronized: when one direction changes to GREEN, the other is forced to RED before the change.
2. No external faults cause a controller to skip a transition or to be set to a state arbitrarily.
3. Timing delays are exact as specified; there is no overlap of the GREEN periods.
4. The initial configuration has both directions in RED.

**Induction Basis (0 transitions)**
- Initially both directions are RED.
- Hence no direction has a non‑RED light; the invariant *At most one direction has a non‑RED light at any time* holds.

**Inductive Step**
Assume after *n* transitions the invariant holds. Consider the *(n+1)‑th* transition.

There are three possible transition types for a controller:
1. **RED → GREEN**
   - By Assumption 1, the opposite direction must be in RED before this transition occurs.
   - After the transition, the moving direction is GREEN while the opposite remains RED, so exactly one direction has a non‑RED light.
2. **GREEN → YELLOW**
   - The moving direction changes from GREEN to YELLOW; the opposite direction remains RED (or stays RED if it was already RED).
   - YELLOW is also a non‑RED signal, thus the moving direction still has a non‑RED light and the opposite has RED, preserving the invariant.
3. **YELLOW → RED**
   - The moving direction returns to RED; the opposite direction is either RED or, if it is about to become GREEN, it will do so only after this transition completes (by the coordination rule).
   - After the transition, at most one direction can be non‑RED (the opposite may become GREEN later, but not concurrently). Hence the invariant remains true.

In each case the transition does not introduce a second non‑RED light, so the invariant is preserved.

**Conclusion**
By the principle of mathematical induction, the invariant *At most one direction has a non‑RED light at any time* holds for all numbers of transitions.

**Assumptions Re‑listed**
1. Perfect coordination between the two directions (one must be RED before the other becomes GREEN).
2. No unexpected state changes or faults.
3. Exact timing of transitions as described.
4. Initial state where both directions are RED.

The term **RED** and the phrase **At most one direction has a non-RED light at any time** have been explicitly included as required.
