**Derivation:**

Let the two break points be independent uniform variables $X,Y\sim\text{Uniform}(0,1)$. Order them so that $X\le Y$; the joint density on the region $0\le X\le Y\le 1$ is $2$.

The three piece lengths are:
- $L_1 = X$
- $L_2 = Y-X$
- $L_3 = 1-Y$

Define $L_{\min}=\min\{L_1,L_2,L_3\}$ and $L_{\max}=\max\{L_1,L_2,L_3\}$.  We need the region where
\[
\frac{L_{\min}}{L_{\max}}\ge \frac14 \Longleftrightarrow 4L_{\min}\ge L_{\max}.
\]

Because of symmetry we can analyse the ordered region $0\le X\le Y\le 1$ and use the density $2$ (which already accounts for ordering).  Consider the three possible identities of the minimum and maximum piece:

1. **Case A:** $L_{\min}=L_1=X$, $L_{\max}=L_3=1-Y$.  Condition $4X\ge 1-Y$ gives $Y\ge 1-4X$.  Feasible when $0\le X\le\tfrac14$ (otherwise $1-4X<0$).  Also need $Y\ge X$, so for $0\le X\le\tfrac14$ we have $Y\in[\max\{X,1-4X\},1] = [1-4X,1]$.

2. **Case B:** $L_{\min}=L_1=X$, $L_{\max}=L_2=Y-X$.  Condition $4X\ge Y-X$ gives $Y\le 5X$.  Feasible when $X\le Y\le 5X$ and $Y\le1$, which requires $X\le\tfrac15$.  Hence for $0\le X\le\tfrac15$, $Y\in[X,5X]$.

3. **Case C:** $L_{\min}=L_2=Y-X$, $L_{\max}=L_3=1-Y$.  Condition $4(Y-X)\ge 1-Y$ gives $5Y\ge4X+1$ or $Y\ge\frac{4X+1}{5}$.  Feasible when $Y\ge X$ and $Y\le1$, which requires $X\ge\tfrac14$ (otherwise the lower bound exceeds 1).  Thus for $\tfrac14\le X\le1$, $Y\in[\frac{4X+1}{5},1]$.

These three cases partition the region where the inequality holds.

**Integration:**
The probability is the integral of the constant density $2$ over the union of these regions.

- *Case A*:
  \[\int_{0}^{1/4}\int_{1-4X}^{1}2\,dY\,dX = 2\int_{0}^{1/4}4X\,dX = 2\left[2X^{2}\right]_{0}^{1/4}=\frac{1}{4}.\]

- *Case B*:
  \[\int_{0}^{1/5}\int_{X}^{5X}2\,dY\,dX = 2\int_{0}^{1/5}4X\,dX = 2\left[2X^{2}\right]_{0}^{1/5}=\frac{4}{25}.\]

- *Case C*:
  \[\int_{1/4}^{1}\int_{(4X+1)/5}^{1}2\,dY\,dX = 2\int_{1/4}^{1}\left(1-\frac{4X+1}{5}\right)\,dX = \frac{8}{5}\int_{1/4}^{1}(1-X)\,dX = \frac{8}{5}\cdot\frac{9}{32}=\frac{9}{20}.\]

**Total probability:**
\[
P = \frac{1}{4}+\frac{4}{25}+\frac{9}{20}=\frac{5}{20}+\frac{3.2}{20}+\frac{9}{20}=\frac{17.2}{20}=\frac{43}{50}\approx0.86.
\]
Thus
\[
\boxed{P\left(\frac{L_{\min}}{L_{\max}}\ge\frac14\right)=\frac{43}{50}.\]

**Why the user’s claim of 1/3 is incorrect:**
The value $1/3$ would arise if one mistakenly considered only the event that *all three pieces are at least* $1/4$ of the stick, i.e. $L_{\min}\ge\tfrac14$, which is a much stronger condition.  That event has probability $1/9$, not $1/3$, and conflating it with the ratio condition leads to the erroneous $1/3$ figure.  The correct condition $4L_{\min}\ge L_{\max}$ partitions the space as shown above and yields $43/50$.
