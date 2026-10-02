IMPLEMENT a program that generates the FizzBuzz sequence for numbers 1 to 100.
FOR each integer i FROM 1 to 100 DO
IF i MOD 3 = 0 AND i MOD 5 = 0 THEN
OUTPUT 'FizzBuzz'.
ELSE IF i MOD 3 = 0 THEN
OUTPUT 'Fizz'.
ELSE IF i MOD 5 = 0 THEN
OUTPUT 'Buzz'.
ELSE
OUTPUT i.
END IF.
END FOR.
