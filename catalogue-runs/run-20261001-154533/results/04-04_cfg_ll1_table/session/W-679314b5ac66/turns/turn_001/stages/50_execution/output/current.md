FIRST sets:
E  : {id, (}
E' : {+, ε}
T  : {id, (}
T' : {*, ε}
F  : {id, (}

FOLLOW sets:
E  : {$, )}
E' : {$, )}
T  : {+, $, )}
T' : {+, $, )}
F  : {*, +, $, )}

LL(1) Parse Table (rows: non‑terminals, columns: terminals id, +, *, (, ), $):

          id      +       *       (       )       $
E   → T E'  T E'               T E'              
E'  → ε                ε      + T E'  ε       ε
T   → F T'  F T'               F T'              
T'  → ε                ε      * F T'  ε       ε
F   → id    id               ( E )

Parse trace for input "id + id * id":

Step  Stack                Input       Action
0   [E,$]                id+id*id$   Expand E→T E'
1   [T',E',$]           id+id*id$   Expand T→F T'
2   [F,T',E',$]         id+id*id$   Expand F→id
3   [id,T',E',$]        id+id*id$   Match id, pop
4   [T',E',$]           +id*id$    Expand T'→ε (since +∈FOLLOW(T'))
5   [E',$]              +id*id$    Expand E'→+ T E'
6   [+ ,T,E',$]         +id*id$    Match +
7   [T,E',$]            id*id$    Expand T→F T'
8   [F,T',E',$]         id*id$    Expand F→id
9   [id,T',E',$]        id*id$    Match id
10  [T',E',$]           *id$      Expand T'→* F T'
11  [*,F,T',E',$]       *id$      Match *
12  [F,T',E',$]         id$       Expand F→id
13  [id,T',E',$]        id$       Match id
14  [T',E',$]           $         Expand T'→ε (since $∈FOLLOW(T'))
15  [E',$]              $         Expand E'→ε (since $∈FOLLOW(E'))
16  [$]                 $         Match $ and accept.

Operative task entities: E, E', T, T', F, id, +, *, (, ), id + id * id
