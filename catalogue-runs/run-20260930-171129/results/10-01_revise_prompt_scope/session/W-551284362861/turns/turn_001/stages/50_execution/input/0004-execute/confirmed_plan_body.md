VALIDATE that input N is an integer greater than or equal to 2
INITIALIZE a boolean array is_prime[0..N] set all entries to true
SET is_prime[0] and is_prime[1] to false
FOR each integer i from 2 up to floor(sqrt(N))
IF is_prime[i] is true THEN
FOR each multiple j of i from i*i to N step i
SET is_prime[j] to false
ENDFOR
ENDIF
ENDFOR
CREATE an empty list primes
FOR each integer k from 2 to N
IF is_prime[k] is true THEN
APPEND k to primes
ENDIF
ENDFOR
RETURN primes
