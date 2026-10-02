def sieve_primes(N):
    """Return a list of all prime numbers up to and including N using the Sieve of Eratosthenes.
    If N is less than 2, an empty list is returned.
    """
    if not isinstance(N, int) or N < 2:
        return []
    # Initialize boolean array where index represents number primality
    is_prime = [True] * (N + 1)
    is_prime[0] = is_prime[1] = False
    import math
    limit = int(math.isqrt(N))
    for p in range(2, limit + 1):
        if is_prime[p]:
            # start marking from p*p
            start = p * p
            is_prime[start:N+1:p] = [False] * len(is_prime[start:N+1:p])
    # Collect primes
    return [i for i, prime in enumerate(is_prime) if prime]
