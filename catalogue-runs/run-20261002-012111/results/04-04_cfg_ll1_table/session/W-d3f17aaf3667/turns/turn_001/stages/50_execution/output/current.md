FIRST sets:
E  = {id, (}
E' = {+, ε}
T  = {id, (}
T' = {*, ε}
F  = {id, (}

FOLLOW sets:
E  = {), $}
E' = {), $}
T  = {+, ), $}
T' = {+, ), $}
F  = {*, +, ), $}

LL(1) Parse Table (rows = non‑terminals, columns = terminals id, +, *, (, ), $):

          id        +        *        (        )        $
----------------------------------------------------------
E   | E→T E'  |          |          | E→T E' |          |   
E'  | ε       | E'→+ T E'|          | ε       | E'→ε   | E'→ε 
T   | T→F T'  |          |          | T→F T' |          |   
T'  | ε       | T'→ε    | T'→* F T'| ε       | T'→ε   | T'→ε 
F   | F→id    |          |          | F→( E )|          |   

Parsing steps for input "id + id * id" (tokens: id + id * id $):

Step 0: Stack [E $]          Input: id + id * id $
Step 1: Expand E → T E'   Stack [E' T $]
Step 2: Expand T → F T'   Stack [T' F E' $]
Step 3: Expand F → id      Stack [id T' E' $]   (match id)
Step 4: Match id           Stack [T' E' $]    Input: + id * id $
Step 5: T' → ε (since + ∈ FOLLOW(T'))   Stack [E' $]
Step 6: Expand E' → + T E' Stack [E' T + $]
Step 7: Match +            Stack [E' T $]     Input: id * id $
Step 8: Expand T → F T'   Stack [T' F E' $]
Step 9: Expand F → id      Stack [id T' E' $]   (match id)
Step10: Match id           Stack [T' E' $]    Input: * id $
Step11: T' → * F T'       Stack [T' F * E' $]
Step12: Match *            Stack [T' F E' $]   Input: id $
Step13: Expand F → id      Stack [id T' E' $]   (match id)
Step14: Match id           Stack [T' E' $]    Input: $ 
Step15: T' → ε (ε ∈ FOLLOW(T')) Stack [E' $]
Step16: E' → ε            Stack [$]          Input: $ 
Step17: $ matches $       Stack []           Input: $ (accepted)
