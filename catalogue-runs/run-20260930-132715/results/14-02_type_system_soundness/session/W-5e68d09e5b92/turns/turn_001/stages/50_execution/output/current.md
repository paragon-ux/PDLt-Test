--- Syntax ---

Expressions e ::= n                       // integer literal
               | true | false            // boolean literals
               | e1 + e2                // addition
               | e1 < e2                // less‑than comparison
               | if e1 then e2 else e3  // conditional

Values   v ::= n                       // integer values
               | true | false          // boolean values

--- Types ---

T ::= Int | Bool

--- Typing rules (Γ ⊢ e : T) ---

(T-Int)      Γ ⊢ n : Int
(T-True)     Γ ⊢ true : Bool
(T-False)    Γ ⊢ false : Bool
(T-Add)      Γ ⊢ e1 : Int   Γ ⊢ e2 : Int
               ------------------------------
               Γ ⊢ e1 + e2 : Int
(T-Lt)       Γ ⊢ e1 : Int   Γ ⊢ e2 : Int
               ------------------------------
               Γ ⊢ e1 < e2 : Bool
(T-If)       Γ ⊢ e1 : Bool   Γ ⊢ e2 : T   Γ ⊢ e3 : T
               -------------------------------------------
               Γ ⊢ if e1 then e2 else e3 : T

--- Small‑step operational semantics (e → e') ---

(Step-IfTrue)   if true then e2 else e3  →  e2
(Step-IfFalse)  if false then e2 else e3 →  e3
(Step-If)       e1 → e1'                →  if e1' then e2 else e3

(Step-Add1)     e1 → e1'                →  e1' + e2
(Step-Add2)     v1 is a value, e2 → e2' →  v1 + e2'   (where v1 is an integer literal)
(Step-Add)      n1 + n2                 →  n where n = n1 + n2 (integer addition)

(Step-Lt1)      e1 → e1'                →  e1' < e2
(Step-Lt2)      v1 is a value, e2 → e2' →  v1 < e2'   (v1 integer)
(Step-Lt)       n1 < n2                 →  true   if n1 < n2
               n1 < n2                 →  false  otherwise

--- Progress Theorem ---

*Theorem (Progress).* If ⊢ e : T then either e is a value or there exists e' such that e → e'.

*Proof by induction on the typing derivation of e.*

1. **Case (T-Int)**: e = n. By definition n is a value. ✓
2. **Case (T-True)**: e = true. true is a value. ✓
3. **Case (T-False)**: e = false. false is a value. ✓
4. **Case (T-Add)**: e = e1 + e2 with ⊢ e1 : Int and ⊢ e2 : Int.
   - By IH, e1 is a value or steps.
     *If e1 steps to e1'*, then by (Step-Add1) e → e1' + e2.
   - Otherwise e1 is a value (an integer n1).
     By IH on e2, either e2 steps to e2' (use (Step-Add2)) or e2 is a value n2.
     If e2 steps, e → n1 + e2' via (Step-Add2).
     If both are values, apply (Step-Add) to obtain the integer result. ✓
5. **Case (T-Lt)**: e = e1 < e2 with ⊢ e1 : Int, ⊢ e2 : Int.
   - Analogous to addition using (Step-Lt1), (Step‑Lt2) and (Step‑Lt). ✓
6. **Case (T-If)**: e = if e1 then e2 else e3 with ⊢ e1 : Bool, ⊢ e2 : T, ⊢ e3 : T.
   - By IH on e1, either e1 is a value or steps.
     *If e1 steps to e1'*, then (Step‑If) gives e → if e1' then e2 else e3.
     *If e1 is a value*, it must be true or false.
       - If true, (Step‑IfTrue) yields e → e2.
       - If false, (Step‑IfFalse) yields e → e3. ✓

All cases satisfy the property: a well‑typed expression is either a value or can take a step. ∎

--- Conclusion ---
Thus every well‑typed expression in the language either is a value or can make a computation step, establishing the Progress theorem for the defined language.
