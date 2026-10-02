DEFINE a model of a dynamic array that starts with capacity 1 and doubles on overflow.
SET bank_balance := 0.
FOR each push operation DO
    IF the array is full THEN
        CHARGE an amortized cost covering the actual push cost and the cost of copying all elements to a new array of double capacity.
        UPDATE bank_balance := bank_balance + (amortized_cost - actual_cost).
    ELSE
        CHARGE an amortized cost covering the actual push cost.
        UPDATE bank_balance := bank_balance + (amortized_cost - actual_cost).
    ENDIF
    ASSERT bank_balance ≥ 0.
ENDFOR
DERIVE an amortized cost per push that satisfies the bank balance constraints.
PROVE that the derived amortized cost is O(1) per push.
COMPUTE the exact amortized cost per operation (to be determined).
