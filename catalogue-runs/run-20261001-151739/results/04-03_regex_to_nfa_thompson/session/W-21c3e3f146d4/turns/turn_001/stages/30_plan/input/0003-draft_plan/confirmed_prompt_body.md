READ the regular expression specification and required features
BUILD a nondeterministic finite automaton (NFA) using Thompson's construction with epsilon transitions without backtracking
SUPPORT concatenation, alternation (|), Kleene star (*), plus (+), optional (?), character classes ([a-z]), dot (.), and grouping with parentheses
IMPLEMENT the solution in Python
PERFORM matching via simultaneous NFA simulation tracking the set of active states
VALIDATE with test cases:
- FOR pattern a(b|c)*d, EXPECT matches for ad, abcd, abcbcd and EXPECT rejection for aed
- FOR pattern [0-9]+, EXPECT matches for 123 and EXPECT rejection for abc
