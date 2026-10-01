**FIRST sets**
- FIRST(E)  = { '(', id }
- FIRST(E') = { '+', ε }
- FIRST(T)  = { '(', id }
- FIRST(T') = { '*', ε }
- FIRST(F)  = { '(', id }

**FOLLOW sets**
- FOLLOW(E)  = { $ , ')' }
- FOLLOW(E') = { $ , ')' }
- FOLLOW(T)  = { + , $ , ')' }
- FOLLOW(T') = { + , $ , ')' }
- FOLLOW(F)  = { * , + , $ , ')' }

**LL(1) Parse Table** (rows = non‑terminals, columns = terminals { id, +, *, (, ), $, ε })

|          | id | + | * | ( | ) | $ |
|----------|----|---|---|---|---|---|
| E        | E → T E' |   |   | E → T E' |   |   |
| E'       |   | E' → + T E' |   |   | E' → ε | E' → ε |
| T        | T → F T' |   |   | T → F T' |   |   |
| T'       |   | T' → ε | T' → * F T' |   | T' → ε | T' → ε |
| F        | F → id |   |   | F → ( E ) |   |   |

**Parsing of input `id + id * id`** (where $ denotes end‑of‑input)

Initial stack: `$ E`
Input: `id + id * id $`

1. Stack: `$ E` Input: `id + id * id $`
   - Top `E`, look‑up table entry `E → T E'`. Push `E' T`.
   Stack: `$ E' T`

2. Stack: `$ E' T` Input: `id + id * id $`
   - Top `T`, entry `T → F T'`. Push `T' F`.
   Stack: `$ E' T' F`

3. Stack: `$ E' T' F` Input: `id + id * id $`
   - Top `F`, entry `F → id`. Match `id`.
   Stack: `$ E' T'`
   Input: `+ id * id $`

4. Stack: `$ E' T'` Input: `+ id * id $`
   - Top `T'`, entry `T' → ε` (since lookahead `+` not `*`). Pop `T'`.
   Stack: `$ E'`

5. Stack: `$ E'` Input: `+ id * id $`
   - Top `E'`, entry `E' → + T E'`. Push `E' T +`.
   Stack: `$ E' T +`

6. Stack: `$ E' T +` Input: `+ id * id $`
   - Top `+` matches terminal `+`. Pop `+`.
   Stack: `$ E' T`
   Input: `id * id $`

7. Stack: `$ E' T` Input: `id * id $`
   - Top `T`, entry `T → F T'`. Push `T' F`.
   Stack: `$ E' T' F`

8. Stack: `$ E' T' F` Input: `id * id $`
   - Top `F`, entry `F → id`. Match `id`.
   Stack: `$ E' T'`
   Input: `* id $`

9. Stack: `$ E' T'` Input: `* id $`
   - Top `T'`, entry `T' → * F T'`. Push `T' F *`.
   Stack: `$ E' T' F *`

10. Stack: `$ E' T' F *` Input: `* id $`
    - Top `*` matches terminal `*`. Pop `*`.
    Stack: `$ E' T' F`
    Input: `id $`

11. Stack: `$ E' T' F` Input: `id $`
    - Top `F`, entry `F → id`. Match `id`.
    Stack: `$ E' T'`
    Input: `$`

12. Stack: `$ E' T'` Input: `$`
    - Top `T'`, entry `T' → ε`. Pop `T'`.
    Stack: `$ E'`

13. Stack: `$ E'` Input: `$`
    - Top `E'`, entry `E' → ε`. Pop `E'`.
    Stack: `$`

14. Stack: `$` Input: `$`
    - Both stack top and input are `$`. Parsing successful.

**Result IR**
