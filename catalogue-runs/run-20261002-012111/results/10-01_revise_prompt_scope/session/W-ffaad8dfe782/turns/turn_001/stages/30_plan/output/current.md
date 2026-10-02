DEFINE the function signature for computing primes up to N
VALIDATE that N is an integer greater than or equal to 2; if not, define appropriate behavior
INITIALIZE a boolean array of size N + 1 and set all entries to true
SET the entries for 0 and 1 to false
FOR each integer p from 2 up to floor(sqrt(N))
  IF the entry for p is true
    MARK all multiples of p starting at p * p up to N as false
  ENDIF
ENDFOR
CREATE an empty list of primes
FOR each index i from 2 to N
  IF the entry for i is true
    APPEND i to the list of primes
  ENDIF
ENDFOR
RETURN the list of primes
