TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Prove that the recursive function collatz_steps terminates for all non-negative integer inputs. The function is defined in Python as:
```
def collatz_steps(n):
    if n <= 1:
        return 0
    elif n % 2 == 0:
        return 1 + collatz_steps(n // 2)
    else:
        return 1 + collatz_steps(3 * n + 1)
``` The request asks for a mathematical proof of termination for every input n ≥ 0, covering all branches and ensuring no infinite recursion occurs.
APPROACH/RISK NOTES:
