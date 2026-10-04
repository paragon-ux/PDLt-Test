```python
def primes_and_twins(limit=100):
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, int(limit ** 0.5) + 1):
        if is_prime[p]:
            for m in range(p * p, limit + 1, p):
                is_prime[m] = False
    primes = [n for n in range(limit + 1) if is_prime[n]]
    twins = sum(1 for a, b in zip(primes, primes[1:]) if b - a == 2)
    return primes, twins

primes, twins = primes_and_twins(100)
print(len(primes), twins)   # 25 8
```
Primes up to 100 (25 of them) and 8 twin-prime pairs.
