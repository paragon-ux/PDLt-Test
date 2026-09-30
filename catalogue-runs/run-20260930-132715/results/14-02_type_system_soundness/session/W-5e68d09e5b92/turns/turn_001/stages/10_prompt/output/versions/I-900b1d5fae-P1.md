DEFINE the small-step operational semantics for the language consisting of integer literals, boolean literals, addition, less-than comparison, and if-then-else constructs.
INCLUDE the syntax categories and value definitions using the operative task entities: n, if, then, else, value, step.
SPECIFY the evaluation rules (step relations) for each construct, ensuring that each rule uses the term "step" where appropriate.
PROVE the Progress theorem: FOR any expression e such that e : T, EITHER e is a value OR there exists an expression e' such that e steps to e'.
STRUCTURALLY INDUCT on the typing derivation of e, covering each typing rule (including those for n, if‑then‑else, addition, and less‑than).
FOR each case, SHOW that either the expression is a value or a applicable step rule applies, producing a successor e'.
STATE the conclusion that all well‑typed expressions satisfy progress.
