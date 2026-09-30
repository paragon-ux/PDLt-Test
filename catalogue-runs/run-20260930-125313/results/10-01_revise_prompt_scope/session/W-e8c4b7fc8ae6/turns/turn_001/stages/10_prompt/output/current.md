READ the integer N from input
CREATE a boolean array is_prime[0..N] initialized to TRUE
SET is_prime[0] and is_prime[1] to FALSE
FOR each integer p from 2 up to floor(sqrt(N)) DO
IF is_prime[p] is TRUE THEN
FOR multiple m from p*p to N step p DO
SET is_prime[m] to FALSE
ENDFOR
ENDIF
ENDFOR
COLLECT all indices i where is_prime[i] is TRUE into list primes
RETURN the list primes
