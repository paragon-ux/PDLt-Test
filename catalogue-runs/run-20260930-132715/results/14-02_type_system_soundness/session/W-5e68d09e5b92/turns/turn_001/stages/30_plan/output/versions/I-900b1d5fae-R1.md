DEFINE syntax categories for integer literals, boolean literals, addition, less‑than, and if‑then‑else constructs using the entities n, if, then, else, value, step
DEFINE value definitions for integer literals and boolean literals
SPECIFY typing rules for each language construct
DEFINE operational step relations (small‑step semantics) for each construct, ensuring each rule uses the term "step"
STRUCTURE a proof of the Progress theorem
INDUCT on the typing derivation of a given expression e
FOR each typing rule case (n, boolean literal, addition, less‑than, if‑then‑else)
IF the expression matches a value form THEN ASSERT it is a value
ELSE APPLY the appropriate step rule to obtain a successor expression e'
CONCLUDE that every well‑typed expression either is a value or can take a step
