Values: v ::= n | true | false.

Small-step semantics:
- (E-Add1) if e1 -> e1' then e1 + e2 -> e1' + e2
- (E-Add2) if e2 -> e2' then v1 + e2 -> v1 + e2'
- (E-Add) n1 + n2 -> n where n = n1 + n2
- (E-Lt1), (E-Lt2) as for +; (E-Lt) n1 < n2 -> true if n1 < n2, else false
- (E-If) if e1 -> e1' then (if e1 then e2 else e3) -> (if e1' then e2 else e3)
- (E-IfTrue) if true then e2 else e3 -> e2; (E-IfFalse) if false then e2 else e3 -> e3

Lemma (canonical forms). If v is a value and v : Bool then v is true or false; if v : Int then v is a literal n. Proof: inspect the typing rules; the only rules that type a value give literals Int and true/false Bool.

Theorem (Progress). If e : T then e is a value or e -> e' for some e'.
Proof by induction on the derivation of e : T.
- T-Int, T-True, T-False: e is a value.
- T-Add: e = e1 + e2 with e1 : Int, e2 : Int. By IH e1 is a value or steps. If e1 steps, E-Add1 applies. If e1 is a value, by IH e2 is a value or steps; if it steps, E-Add2 applies; if both are values, canonical forms makes them literals n1, n2 and E-Add applies.
- T-Lt: identical, ending with E-Lt.
- T-If: e = if e1 then e2 else e3 with e1 : Bool. By IH e1 steps (E-If applies) or is a value; then by canonical forms e1 is true or false and E-IfTrue or E-IfFalse applies.
Every case either is a value or steps. QED.
