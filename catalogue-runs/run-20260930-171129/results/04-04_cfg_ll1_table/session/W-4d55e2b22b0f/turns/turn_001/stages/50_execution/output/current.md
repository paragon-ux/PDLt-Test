FIRST sets:
E  = {id, (}
E' = {+, epsilon}
T  = {id, (}
T' = {*, epsilon}
F  = {id, (}

FOLLOW sets:
E  = {$, )}
E' = {$, )}
T  = {+, $, )}
T' = {+, $, )}
F  = {*, +, $, )}

LL(1) parse table (rows = non‑terminals, columns = terminals id, +, *, (, ), $):

          id      +      *      (      )      $
E   |  E→T E'  -      -   E→T E'  -      -
E'  |   -    E'→+ T E'  -   -   E'→ε  E'→ε
T   |  T→F T'  -      -   T→F T'  -      -
T'  |   -    T'→ε  T'→* F T'  -   T'→ε  T'→ε
F   |  F→id   -      -   F→( E )  -      -

Parsing trace for input id + id * id $ (stack shown top on the left):

Step 0: Stack: $ E          Input: id + id * id $
Step 1: Stack: $ E' T       (E → T E')   Input: id + id * id $
Step 2: Stack: $ E' T' F    (T → F T')   Input: id + id * id $
Step 3: Stack: $ E' T' id   (F → id)      Input: id + id * id $
Match id, pop id, advance input.
Step 4: Stack: $ E' T'      Input: + id * id $
Top T' is epsilon (from FOLLOW), pop T'.
Step 5: Stack: $ E'         Input: + id * id $
Top E' → + T E' (since input '+')
Stack after push: $ E' T +
Step 6: Stack: $ E' T +      Input: + id * id $
Match '+', pop '+', advance.
Step 7: Stack: $ E' T        Input: id * id $
Apply T → F T'
Stack: $ E' T' F
Step 8: Stack: $ E' T' id   Input: id * id $
Match id, pop, advance.
Step 9: Stack: $ E' T'      Input: * id $
Top T' → * F T'
Stack: $ E' T' T' F *
Step 10: Stack: $ E' T' T' F *   Input: * id $
Match '*', pop, advance.
Step 11: Stack: $ E' T' T' F   Input: id $
Apply F → id
Stack: $ E' T' T' id
Match id, pop, advance.
Step 12: Stack: $ E' T' T'   Input: $ (end)
Top T' epsilon, pop.
Step 13: Stack: $ E' T'   Input: $
Top T' epsilon, pop.
Step 14: Stack: $ E'   Input: $
Top E' epsilon, pop.
Step 15: Stack: $   Input: $
Both stack and input at end marker – input ACCEPTED.

The input string "id + id * id" is successfully parsed according to the constructed LL(1) table.
