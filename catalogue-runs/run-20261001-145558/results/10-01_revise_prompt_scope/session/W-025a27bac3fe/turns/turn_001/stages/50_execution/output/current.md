def sieve_primes(N: int) -> list[int]:
    """Return a list of all prime numbers up to N using the Sieve of Eratosthenes.
    
    Args:
        N: The inclusive upper bound for prime generation. Must be a non‑negative integer.
    
    Returns:
        A list of prime numbers <= N.
    """
    if N < 2:
        return []
    # Initialize boolean array where index represents number primality
    is_prime = [True] * (N + 1)
    is_prime[0] = is_prime[1] = False
    p = 2
    while p * p <= N:
        if is_prime[p]:
            # Mark multiples of p as non‑prime
            for multiple in range(p * p, N + 1, p):
                is_prime[multiple] = False
        p += 1
    # Collect all primes
    return [i for i, prime in enumerate(is_prime) if prime]
