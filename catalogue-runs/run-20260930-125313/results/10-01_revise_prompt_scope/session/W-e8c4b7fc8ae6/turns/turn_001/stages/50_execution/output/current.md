def sieve_of_erasthenes(N: int) -> list[int]:
    """Return a list of all prime numbers up to and including N using the Sieve of Eratosthenes."""
    if N < 2:
        return []
    # INITIALIZE a boolean array is_prime[0..N] set to TRUE
    is_prime = [True] * (N + 1)
    # SET is_prime[0] and is_prime[1] to FALSE
    is_prime[0] = is_prime[1] = False
    # FOR each integer p from 2 up to floor(sqrt(N)) DO
    p = 2
    while p * p <= N:
        # IF is_prime[p] is TRUE THEN
        if is_prime[p]:
            # FOR each multiple m from p*p to N stepping by p DO
            for m in range(p * p, N + 1, p):
                # SET is_prime[m] to FALSE
                is_prime[m] = False
        # ENDIF
        p += 1
    # ENDFOR
    # COLLECT all indices i where is_prime[i] is TRUE into list primes
    primes = [i for i, prime in enumerate(is_prime) if prime]
    # RETURN the list primes
    return primes

# Example usage (can be removed in production)
if __name__ == "__main__":
    print(sieve_of_erasthenes(30))
