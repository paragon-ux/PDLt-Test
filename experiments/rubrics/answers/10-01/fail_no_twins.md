```python
def sieve(n=100):
    flags = [True] * (n + 1); flags[0] = flags[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if flags[i]:
            flags[i * i::i] = [False] * len(flags[i * i::i])
    return [i for i, f in enumerate(flags) if f]
```
Returns the 25 primes up to 100.
