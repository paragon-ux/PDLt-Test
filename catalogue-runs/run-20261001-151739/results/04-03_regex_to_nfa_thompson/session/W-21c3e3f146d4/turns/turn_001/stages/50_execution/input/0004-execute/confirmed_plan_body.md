READ the regular expression specification and required features
BUILD a nondeterministic finite automaton (NFA) using Thompson's construction with epsilon transitions
SUPPORT concatenation, alternation (|), Kleene star (*), plus (+), optional (?), character classes ([a-z]), dot (.), and grouping parentheses
IMPLEMENT the NFA builder and simulator in Python
PERFORM matching by simultaneous NFA simulation tracking the set of active states
VALIDATE the implementation with the test cases:
- FOR pattern a(b|c)*d, EXPECT matches for ad, abcd, abcbcd and EXPECT rejection for aed
- FOR pattern [0-9]+, EXPECT matches for 123 and EXPECT rejection for abc
