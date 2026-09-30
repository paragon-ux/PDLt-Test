READ the dynamic array operations starting with capacity 1
FOR each PUSH operation
IF the push exceeds current capacity THEN
RESIZE the array to double its current capacity
COPY all existing elements (cost equal to number of elements before resize)
ENDIF
ACCOUNT for the push cost of 1 unit
ASSIGN an amortized cost per operation using the accounting (banker's) method so that the prepaid credit balance never becomes negative
ENSURE the amortized cost is O(1) and compute its exact value per push
PROVE that the credit invariant holds for all sequence lengths
ENDFOR
