IMPLEMENT Thompson's construction in Python to convert a regular expression to an NFA.
SUPPORT concatenation, alternation (|), Kleene star (*), plus (+), optional (?), character classes ([a-z]), dot (.), and grouping with parentheses.
BUILD the NFA using epsilon transitions without backtracking.
PERFORM matching via simultaneous NFA simulation tracking the set of active states.
INCLUDE tests verifying that the pattern a(b|c)*d matches ad, abcd, abcbcd and does not match aed; and that the pattern [0-9]+ matches 123 and does not match abc.
