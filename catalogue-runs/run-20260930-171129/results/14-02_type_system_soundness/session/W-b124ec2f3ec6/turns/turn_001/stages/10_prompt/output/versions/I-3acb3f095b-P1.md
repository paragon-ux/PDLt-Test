DEFINE the small-step operational semantics for the tiny language consisting of integer literals, boolean literals, addition, less‑than, and conditional expressions using the syntax constructs n, if, then, else, and type annotation T.
PROVIDE the typing rules for expressions of type T.
STATE the Progress theorem: FOR any expression e, IF the typing judgment e : T holds, THEN either e is a value (integer literal or boolean literal) OR there exists an expression e' such that e → e'.
PROVE the Progress theorem by STRUCTURAL INDUCTION on the typing derivation of e, covering each typing rule case.
