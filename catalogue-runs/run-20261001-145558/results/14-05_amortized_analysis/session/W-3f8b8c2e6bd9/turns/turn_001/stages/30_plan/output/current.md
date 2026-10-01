DEFINE the accounting method for the dynamic array using a potential function based on current capacity and size
ASSIGN an initial potential of zero when the array capacity is 1 and empty
FOR each PUSH operation DO
    IF the push does not exceed current capacity THEN
        CHARGE the actual cost of the push
        UPDATE the potential according to the new size
    ELSE
        CHARGE the actual cost of copying all existing elements plus the push
        DOUBLE the capacity
        UPDATE the potential to reflect the new capacity and size
    ENDIF
    COMPUTE the amortized cost as actual cost plus change in potential
ENDFOR
VERIFY that the amortized cost computed for any push is bounded by a constant, establishing O(1) amortized time per push
PROVE that the potential (bank balance) is never negative by showing that the initial potential is zero and the update rule always yields a non‑negative value
DERIVE the exact amortized cost per operation from the accounting equations established
