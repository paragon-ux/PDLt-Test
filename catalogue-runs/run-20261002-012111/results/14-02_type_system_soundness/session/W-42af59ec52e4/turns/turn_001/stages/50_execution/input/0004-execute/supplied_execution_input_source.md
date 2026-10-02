Consider the following simple type system for a tiny language with integers, booleans, and an if-then-else expression:

Types: Int, Bool
Expressions: n (integer literal), true, false, e1 + e2, e1 < e2, if e1 then e2 else e3
Typing rules:
  - n : Int
  - true : Bool, false : Bool
  - If e1 : Int and e2 : Int, then e1 + e2 : Int
  - If e1 : Int and e2 : Int, then e1 < e2 : Bool
  - If e1 : Bool and e2 : T and e3 : T, then (if e1 then e2 else e3) : T

Prove the Progress theorem: if an expression e is well-typed (e : T), then either e is a value or there exists an expression e' such that e steps to e'. Define the small-step operational semantics and give the proof by structural induction on the typing derivation.
