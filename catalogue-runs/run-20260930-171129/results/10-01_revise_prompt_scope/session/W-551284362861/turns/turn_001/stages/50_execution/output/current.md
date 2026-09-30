def sieve_of_eratosthenes(N: int) -> list[int]:
    """Return list of prime numbers up to N using the Sieve of Eratosthenes."""
    if N < 2:
        return []
    is_prime = [True] * (N + 1)
    is_prime[0] = is_prime[1] = False
    import math
    for i in range(2, int(math.isqrt(N)) + 1):
        if is_prime[i]:
            for j in range(i * i, N + 1, i):
                is_prime[j] = False
    return [i for i, prime in enumerate(is_prime) if prime]

# Example usage:
# print(sieve_of_eratosthenes(30))
