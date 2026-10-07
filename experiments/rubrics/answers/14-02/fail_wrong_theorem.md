We prove that evaluation preserves types (Preservation): if e : T and e -> e' then e' : T.

Semantics: n1 + n2 -> n, n1 < n2 -> b, if true then e2 else e3 -> e2, if false then e2 else e3 -> e3, plus congruence rules.

By induction on the derivation of e -> e': for E-Add the result is a literal of type Int; for E-Lt a boolean of type Bool; for E-IfTrue the result e2 has type T by the typing of if; the congruence cases follow from the induction hypothesis. Hence types are preserved, which shows the system is sound.
