READ the dynamic array push sequence specification
FOR each PUSH operation in the sequence
IF the push would exceed current capacity THEN
ASSIGN a prepaid credit of 2 units to each existing element (banker’s credit) to cover the future resize copy cost
UPDATE the credit balance accordingly
ENDIF
CHARGE the push operation 1 unit of actual cost
APPLY the prepaid credit to pay for any copy work incurred by a resize
ENDFOR
CALCULATE the total prepaid credit per push operation
DERIVE the exact amortized cost that keeps the credit balance non‑negative for any sequence length
STATE the amortized cost as O(1) and provide its numeric value per push
PROVE that the credit invariant (balance never negative) holds for all possible sequence lengths
