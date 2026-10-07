FIRST: FIRST(F) = {(, id}; FIRST(T) = {(, id}; FIRST(E) = {(, id}; FIRST(E') = {+, ε}; FIRST(T') = {*, ε}.
FOLLOW: FOLLOW(E) = {), $}; FOLLOW(E') = {), $}; FOLLOW(T) = {+, ), $}; FOLLOW(T') = {+, ), $}; FOLLOW(F) = {+, *, ), $}.

| NT | id | + | * | ( | ) | $ |
|---|---|---|---|---|---|---|
| E | E→TE' | | | E→TE' | | |
| E' | | E'→+TE' | | | E'→ε | E'→ε |
| T | T→FT' | | | T→FT' | | |
| T' | | T'→ε | T'→*FT' | | T'→ε | T'→ε |
| F | F→id | | | F→(E) | | |

Trace (stack top on the left):
1. E $ | id+id*id$ | E→TE'
2. T E' $ | id+id*id$ | T→FT'
3. F T' E' $ | id+id*id$ | F→id
4. id T' E' $ | id+id*id$ | match id
5. T' E' $ | +id*id$ | T'→ε
6. E' $ | +id*id$ | E'→+TE'
7. + T E' $ | +id*id$ | match +
8. T E' $ | id*id$ | T→FT'
9. F T' E' $ | id*id$ | F→id
10. id T' E' $ | id*id$ | match id
11. T' E' $ | *id$ | T'→*FT'
12. * F T' E' $ | *id$ | match *
13. F T' E' $ | id$ | F→id
14. id T' E' $ | id$ | match id
15. T' E' $ | $ | T'→ε
16. E' $ | $ | E'→ε
17. $ | $ | accept
