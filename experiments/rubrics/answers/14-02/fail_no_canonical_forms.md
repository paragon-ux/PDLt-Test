Values are numbers and booleans. Evaluation reduces + to the sum, < to a boolean and if to its branch.

Proof by induction on the typing derivation. Literals are values. For e1 + e2, by the induction hypothesis e1 and e2 are values or step; if they step, e steps; otherwise e reduces to the sum. The < case is the same. For if e1 then e2 else e3, e1 steps or is a value, and then e reduces to a branch. So every well-typed expression is a value or steps.
