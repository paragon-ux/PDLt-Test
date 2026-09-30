Proof of Invariant Preservation

**Base Case** (VERIFY):
Initially, direction A is in state RED and direction B is in state RED. Therefore, at most one direction has a non‑RED light (in fact none). The invariant holds.

**Inductive Step** (ASSUME):
Assume that after *k* transitions the invariant holds: at most one direction is non‑RED.

**Transition Analysis** (FOR each possible transition from the k‑th state):
1. **A transitions RED → GREEN** (direction A becomes GREEN, B must be RED by controller rule). The invariant holds because only A is non‑RED.
2. **A transitions GREEN → YELLOW** (A becomes YELLOW, B remains RED). YELLOW is a non‑RED colour, but B is still RED, so the invariant holds.
3. **A transitions YELLOW → RED** (A returns to RED, B may now transition to GREEN). After A is RED, the controller permits B to move to GREEN while A is RED, again giving at most one non‑RED direction.
4. **B transitions RED → GREEN** (allowed only when A is RED). Hence only B is non‑RED.
5. **B transitions GREEN → YELLOW** (B becomes YELLOW, A stays RED). Invariant holds.
6. **B transitions YELLOW → RED** (both return to RED). Invariant holds.

**Assumptions** (IDENTIFY):
- The two directions never change state simultaneously; a transition in one direction occurs only after the other is in RED.
- The colour YELLOW is considered non‑RED for the purpose of the invariant.
- The controller enforces mutually exclusive green phases (when one direction is GREEN, the other is forced to RED).

**Conclusion** (CONCLUDE):
Since the invariant holds in the base case and is preserved by every possible transition under the stated assumptions, by mathematical induction the invariant "At most one direction has a non‑RED light at any time" holds for any number of transitions.

---
Result IR
---
{"files":[{"filename":"invariant_proof.txt","satisfies":["R1","R2","R3","R4","R5"],"evidence":{"path":"execution://body","section":"Proof of Invariant Preservation","observed":"Proof of Invariant Preservation"}}],"reconciliation":[{"requirement":"R1","status":"satisfied","evidence":{"path":"execution://body","section":"Base Case (VERIFY):","observed":"Base Case (VERIFY):"}},{"requirement":"R2","status":"satisfied","evidence":{"path":"execution://body","section":"Inductive Step (ASSUME):","observed":"Inductive Step (ASSUME):"}},{"requirement":"R3","status":"satisfied","evidence":{"path":"execution://body","section":"Transition Analysis (FOR each possible transition):","observed":"Transition Analysis (FOR each possible transition):"}},{"requirement":"R4","status":"satisfied","evidence":{"path":"execution://body","section":"Assumptions (IDENTIFY):","observed":"Assumptions (IDENTIFY):"}},{"requirement":"R5","status":"satisfied","evidence":{"path":"execution://body","section":"Conclusion (CONCLUDE):","observed":"Conclusion (CONCLUDE):"}}],"open_defects":[]}
