DEFINE the small-step operational semantics for the language with integer literals, boolean literals, addition, less-than, and if‑then‑else expressions.
SPECIFY the syntax of expressions and values.
DESCRIBE the evaluation relation using inference rules for each construct, including the IF‑THEN‑ELSE rule that uses the keywords if, then, else.
PROVE the Progress theorem: FOR any well‑typed expression e of type T, EITHER e is a value OR there exists e' such that e → e'.
STRUCT the proof BY structural induction on the typing derivation.
FOR each typing case, SHOW that either the expression is a value or a reduction step exists according to the semantics defined above.
ENSURE the proof covers all expression forms, including the if‑then‑else construct.
OUTPUT the theorem statement and the complete inductive proof without performing any evaluation or code execution.
