READ the specification for Thompson's construction in Python
IMPLEMENT a converter that transforms a regular expression into an NFA using epsilon transitions
SUPPORT concatenation, alternation (|), Kleene star (*), plus (+), optional (?), character classes ([a-z]), dot (.), and grouping with parentheses
BUILD the NFA according to Thompson's construction without backtracking
SIMULATE the NFA using simultaneous NFA simulation to match strings by tracking the set of active states
INCLUDE tests verifying that "a(b|c)*d" matches "ad", "abcd", "abcbcd" but not "aed"
INCLUDE tests verifying that "[0-9]+" matches "123" but not "abc"
