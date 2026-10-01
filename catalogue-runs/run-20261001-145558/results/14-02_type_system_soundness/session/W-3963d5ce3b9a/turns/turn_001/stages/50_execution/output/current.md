**Syntax**

*Types* \(T\) ::= \(Int\) | \(Bool\)

*Expressions* \(e\) ::= \(n\)            \(integer literal\)
\(\mid\) \(true\) | \(false\)                \(boolean literals\)
\(\mid\) \(e_1 + e_2\)                     \(addition\)
\(\mid\) \(e_1 < e_2\)                     \(less‑than\)
\(\mid\) \(if\; e_1\; then\; e_2\; else\; e_3\)   \(conditional\)

*Values* \(v\) ::= \(n\) | \(true\) | \(false\)

**Small‑step Operational Semantics** (→)

1. **Addition**
   - \(e_1 \rightarrow e_1'\) \(\displaystyle \frac{}{e_1 + e_2 \rightarrow e_1' + e_2}\)
   - \(e_2 \rightarrow e_2'\) \(\displaystyle \frac{}{n_1 + e_2 \rightarrow n_1 + e_2'}\)   (when \(e_1\) is a value)
   - \(n_1 + n_2 \rightarrow n_3\) where \(n_3\) is the integer sum of \(n_1\) and \(n_2\).

2. **Less‑than**
   - \(e_1 \rightarrow e_1'\) \(\displaystyle \frac{}{e_1 < e_2 \rightarrow e_1' < e_2}\)
   - \(e_2 \rightarrow e_2'\) \(\displaystyle \frac{}{n_1 < e_2 \rightarrow n_1 < e_2'}\)   (when \(e_1\) is a value)
   - \(n_1 < n_2 \rightarrow b\) where \(b\) is \(true\) iff \(n_1 < n_2\), otherwise \(false\).

3. **If‑then‑else**
   - \(e_1 \rightarrow e_1'\) \(\displaystyle \frac{}{if\; e_1\; then\; e_2\; else\; e_3 \rightarrow if\; e_1'\; then\; e_2\; else\; e_3}\)
   - \(if\; true\; then\; e_2\; else\; e_3 \rightarrow e_2\)
   - \(if\; false\; then\; e_2\; else\; e_3 \rightarrow e_3\)

**Typing Rules** (⊢)

- \(\Gamma \vdash n : Int\)
- \(\Gamma \vdash true : Bool\)  \(\Gamma \vdash false : Bool\)
- \(\Gamma \vdash e_1 : Int \; \Gamma \vdash e_2 : Int \;\Rightarrow\; \Gamma \vdash e_1 + e_2 : Int\)
- \(\Gamma \vdash e_1 : Int \; \Gamma \vdash e_2 : Int \;\Rightarrow\; \Gamma \vdash e_1 < e_2 : Bool\)
- \(\Gamma \vdash e_1 : Bool \; \Gamma \vdash e_2 : T \; \Gamma \vdash e_3 : T \;\Rightarrow\; \Gamma \vdash if\; e_1\; then\; e_2\; else\; e_3 : T\)

**Progress Theorem**

*Statement*: If \(\emptyset \vdash e : T\) then either \(e\) is a value or there exists \(e'\) such that \(e \rightarrow e'\).

*Proof* (by structural induction on the typing derivation):

- **Case** \(n\) (integer literal). By the definition of values, \(n\) is a value.
- **Case** \(true\) or \(false\). Both are values.
- **Case** \(e_1 + e_2\) with \(\vdash e_1 : Int\) and \(\vdash e_2 : Int\).
  By the induction hypothesis, either \(e_1\) is a value or it steps.
  * If \(e_1 \rightarrow e_1'\) then by the first addition rule \(e_1 + e_2 \rightarrow e_1' + e_2\).
  * Otherwise \(e_1\) is a value (hence an integer \(n_1\)). Apply the induction hypothesis to \(e_2\):
    - If \(e_2 \rightarrow e_2'\) then \(n_1 + e_2 \rightarrow n_1 + e_2'\) by the second rule.
    - Otherwise \(e_2\) is a value (an integer \(n_2\)). Then the third rule yields a step \(n_1 + n_2 \rightarrow n_3\).
  In all sub‑cases a step exists.
- **Case** \(e_1 < e_2\) analogous to addition, using the less‑than rules.
- **Case** \(if\; e_1\; then\; e_2\; else\; e_3\) with \(\vdash e_1 : Bool\), \(\vdash e_2 : T\), \(\vdash e_3 : T\).
  By induction on \(e_1\):
  * If \(e_1 \rightarrow e_1'\) then the first if‑rule gives a step.
  * Otherwise \(e_1\) is a value. Since it has type \(Bool\), it must be either \(true\) or \(false\). The second or third if‑rule reduces the whole expression to \(e_2\) or \(e_3\) respectively.
  Hence a step exists when the expression is not already a value.

All possible typing forms have been covered; in each case the expression is either a value or can take a reduction step. ∎
