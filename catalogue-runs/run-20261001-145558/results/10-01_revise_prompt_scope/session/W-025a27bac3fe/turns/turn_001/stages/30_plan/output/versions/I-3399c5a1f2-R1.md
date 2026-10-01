READ the request to implement a prime-finding function up to N using the Sieve of Eratosthenes
WRITE a function named sieve_primes that accepts an integer N
INITIALIZE a boolean array of size N+1 set to true for potential primality
MARK indices 0 and 1 as non‑prime
FOR each integer p from 2 up to the square root of N
    IF the array entry for p is true
        MARK all multiples of p greater than p as non‑prime
ENDFOR
COLLECT all indices marked as prime into a list
RETURN the list of primes as the function output
