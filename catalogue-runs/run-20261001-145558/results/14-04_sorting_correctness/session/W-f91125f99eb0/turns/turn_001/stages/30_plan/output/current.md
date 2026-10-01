BASE CASE: ESTABLISH termination for empty list and single-element list
BASE CASE: VERIFY sortedness and permutation properties for empty and single-element lists
INDUCTIVE STEP: ASSUME termination, sortedness, and permutation for lists of length ≤ n
INDUCTIVE STEP: PROVE termination for length n+1 using recursive calls on halves
INDUCTIVE STEP: PROVE sortedness of the output using merge subroutine correctness
INDUCTIVE STEP: PROVE permutation property using merge subroutine correctness
SUB-PROOF: ESTABLISH merge subroutine merges two sorted lists into a sorted list and preserves permutation of their concatenation
DOCUMENT each step, referencing the induction hypothesis where appropriate
DO NOT perform the proofs, only specify that they must be carried out
