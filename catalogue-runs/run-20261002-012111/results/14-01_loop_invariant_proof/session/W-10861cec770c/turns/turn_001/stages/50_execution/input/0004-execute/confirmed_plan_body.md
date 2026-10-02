READ the supplied Python function `array_sum`
PARSE the function to locate the loop iterating over `arr`
IDENTIFY a loop invariant that relates the cumulative sum variable to the elements of `arr` processed so far
PROVE the loop invariant
  ADDRESS initialization: SHOW the invariant holds before the first iteration
  ADDRESS maintenance: SHOW that if the invariant holds before an iteration, it also holds after the iteration body
  ADDRESS termination: SHOW that when the loop exits, the invariant implies the correct final sum
GENERATE a modified version of `array_sum`
  INSERT ASSERT statements at the start of each iteration that verify the invariant
  PRESERVE the original functionality while embedding the asserts
