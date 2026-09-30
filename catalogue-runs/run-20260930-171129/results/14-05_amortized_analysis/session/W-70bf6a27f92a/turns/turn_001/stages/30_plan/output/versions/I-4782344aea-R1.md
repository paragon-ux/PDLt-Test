READ the dynamic array push specification with initial capacity 1 and doubling rule
ASSIGN each push operation an amortized credit of 3 units
FOR each push operation DO
IF the push does NOT exceed current capacity THEN
SPEND 1 unit for the push
ACCUMULATE remaining 2 credit units in the prepaid balance
ELSE
SPEND 1 unit for the push that triggers resize
SPEND n units to copy the n existing elements
USE stored credits to pay the copy cost
ADD remaining credit units to the prepaid balance
ENDIF
ENDFOR
VERIFY that the prepaid credit balance never becomes negative throughout the sequence
SUM the actual costs of all pushes and compare to the total amortized credits assigned
DEDUCE that the total actual cost is bounded by a constant multiple of the number of pushes
INFER that the amortized cost per push is O(1)
CALCULATE the exact amortized cost per operation as the assigned 3 units
