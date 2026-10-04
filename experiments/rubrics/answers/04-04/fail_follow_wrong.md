FIRST(E) = FIRST(T) = FIRST(F) = {(, id}; FIRST(E') = {+, ε}; FIRST(T') = {*, ε}.
FOLLOW(E) = {), $}; FOLLOW(E') = {), $}; FOLLOW(T) = {+, $}; FOLLOW(T') = {+, $}; FOLLOW(F) = {*, $}.

Table: E: id,( → TE'. E': + → +TE', ) → ε, $ → ε. T: id,( → FT'. T': + → ε, * → *FT', $ → ε. F: id → id, ( → (E).

Trace: E$ → TE'$ → FT'E'$ → id T'E'$ (match) → T'E'$ on + → E'$ → +TE'$ (match) → TE'$ → FT'E'$ → id (match) → T' on * → *FT' (match) → F → id (match) → T' on $ → ε → E' on $ → ε → accept.
