The probability can be expressed as the following integral over the ordered cut points 0\leq X\leq Y\leq 1:

P = 6 \int_{0}^{1}\int_{X}^{1} \mathbf{1}\Bigg(\frac{\min\{X,\,Y-X,\,1-Y\}}{\max\{X,\,Y-X,\,1-Y\}} \ge \frac{1}{4}\Bigg)\,dY\,dX

where \mathbf{1}(\cdot) is the indicator function (1 when the condition holds, 0 otherwise). The factor 6 accounts for the six permutations of the unordered cut points. This integral fully defines the desired symbolic probability expression without evaluating it numerically.
