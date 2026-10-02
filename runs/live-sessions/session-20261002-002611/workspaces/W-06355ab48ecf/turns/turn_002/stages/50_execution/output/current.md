**Derivation:**

Let the two break points be independent uniform variables $X,Y\sim\text{Uniform}(0,1)$.  Order them so that $X\le Y$; the joint density on the region $0\le X\le Y\le 1$ is $2$.

The three piece lengths are:
- $L_1 = X$
- $L_2 = Y-X$
- $L_3 = 1-Y$

Define $L_{\min}=\min\{L_1,L_2,L_3\}$ and $L_{\max}=\max\{L_1,L_2,L_3\}$.  We need the region where
\[
\frac{L_{\min}}{L_{\max}}\ge \frac14 \quad\Longleftrightarrow\quad 4L_{\min}\ge L_{\max}.
\]

Because of symmetry we can analyze the ordered region $0\le X\le Y\le 1$ and multiply by $2$ (the density already accounts for ordering).  Consider the three possible identities of the minimum and maximum piece:

1. **Case A:** $L_{\min}=L_1=X$ and $L_{\max}=L_3=1-Y$.  Condition $4X\ge 1-Y$ gives $Y\ge 1-4X$.  Feasible when $0\le X\le\tfrac14$ (otherwise $1-4X<0$).  Also need $X\le Y$, i.e. $Y\ge X$.  Hence for $0\le X\le\tfrac14$, $Y$ ranges from $\max\{X,1-4X\}$ to $1$.

2. **Case B:** $L_{\min}=L_1=X$ and $L_{\max}=L_2=Y-X$.  Condition $4X\ge Y-X$ gives $Y\le 5X$.  Feasible when $X\le Y\le 5X$ and $Y\le 1$.  This requires $X\le \tfrac15$, otherwise $5X>1$ and the upper bound becomes $1$.  So for $0\le X\le \tfrac15$, $Y$ ranges from $X$ to $5X$.

3. **Case C:** $L_{\min}=L_2=Y-X$ and $L_{\max}=L_3=1-Y$.  Condition $4(Y-X)\ge 1-Y$ gives $5Y\ge 4X+1$ or $Y\ge \frac{4X+1}{5}$.  Feasible when $Y\ge X$ and $Y\le 1$.  This requires $X\ge \tfrac14$, because for $X<\tfrac14$ the right‑hand side exceeds $1$.  Thus for $\tfrac14\le X\le 1$, $Y$ ranges from $\max\{X,\frac{4X+1}{5}\}=\frac{4X+1}{5}$ to $1$.

The region for case B (where the maximum is $L_2$) is already covered by case A when $X$ is small, but the three cases partition the valid set without overlap.

**Integration:**
The probability is the integral of the constant density $2$ over the union of these regions.

- *Case A* (minimum $L_1$, maximum $L_3$):
  \[\int_{0}^{1/4}\int_{\max\{X,1-4X\}}^{1} 2\,dY\,dX.
  \]
  For $0\le X\le\tfrac14$, $1-4X\ge X$, so the inner lower bound is $1-4X$.  Hence:
  \[2\int_{0}^{1/4} (1-(1-4X))\,dX = 2\int_{0}^{1/4} 4X\,dX = 2\left[2X^{2}\right]_{0}^{1/4}=2\cdot 2\cdot \frac{1}{16}=\frac{1}{4}.\]

- *Case B* (minimum $L_1$, maximum $L_2$):
  \[\int_{0}^{1/5}\int_{X}^{5X} 2\,dY\,dX = 2\int_{0}^{1/5} (5X-X)\,dX = 2\int_{0}^{1/5}4X\,dX = 2\left[2X^{2}\right]_{0}^{1/5}=2\cdot 2\cdot \frac{1}{25}=\frac{4}{25}.\]

- *Case C* (minimum $L_2$, maximum $L_3$):
  \[\int_{1/4}^{1}\int_{(4X+1)/5}^{1} 2\,dY\,dX = 2\int_{1/4}^{1} \left(1-\frac{4X+1}{5}\right)\,dX = 2\int_{1/4}^{1} \frac{4-4X}{5}\,dX = \frac{8}{5}\int_{1/4}^{1} (1-X)\,dX.
  \]
  Evaluate the last integral:
  \[\int_{1/4}^{1} (1-X)\,dX = \left[ X - \tfrac{X^{2}}{2}\right]_{1/4}^{1}=\left(1-\tfrac12\right)-\left(\tfrac14-\tfrac{1}{32}\right)=\tfrac12-\tfrac{8}{32}+\tfrac{1}{32}=\tfrac{16-8+1}{32}=\tfrac{9}{32}.
  \]
  Therefore the contribution is $\frac{8}{5}\cdot \frac{9}{32}=\frac{72}{160}=\frac{9}{20}$.

**Total probability:**
\[P = \frac{1}{4}+\frac{4}{25}+\frac{9}{20}=\frac{5}{20}+\frac{3.2}{20}+\frac{9}{20}=\frac{5+3.2+9}{20}=\frac{17.2}{20}=\frac{86}{100}=0.86.\]

Simplifying the fractions exactly:
\[\frac{1}{4}=\frac{5}{20},\quad \frac{4}{25}=\frac{3.2}{20}=\frac{16}{100}=\frac{8}{50}=\frac{16}{100},\quad \frac{9}{20}=\frac{45}{100}.\]
Adding gives $\frac{25+16+45}{100}=\frac{86}{100}=\frac{43}{50}$.

Thus the probability that $L_{\min}/L_{\max}\ge \tfrac14$ is **$\displaystyle \frac{43}{50}=0.86$**.

**Answer:** $\boxed{\frac{43}{50}}$.
