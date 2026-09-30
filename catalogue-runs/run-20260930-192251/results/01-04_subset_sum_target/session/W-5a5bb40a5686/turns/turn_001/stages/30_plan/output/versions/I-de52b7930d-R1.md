READ the set S and the target sum T
DEFINE a recursive BACKTRACK procedure that takes the current index, current subset, and running sum
AT each call, IF the running sum equals T THEN EMIT the current subset as a solution and VERIFY its sum
ELSE IF the running sum exceeds T OR the index is beyond the last element THEN RETURN (prune this branch)
ELSE
RECURSE by INCLUDING the element at the current index, updating the subset and running sum
RECURSE by EXCLUDING the element at the current index, leaving the subset and running sum unchanged
END
AFTER the BACKTRACK completes, COUNT all emitted subsets
REPORT the total number of solutions found
