IMPLEMENT Thompson's construction in Python to convert a regular expression to an NFA.
SUPPORT concatenation, alternation (|), Kleene star (*), plus (+), optional (?), character classes ([a-z]), dot (.), and grouping with parentheses.
BUILD the NFA using epsilon transitions only, without backtracking.
SIMULATE the NFA by tracking the set of active states during matching.
INCLUDE unit tests that VERIFY the regular expression "a(b|c)*d" MATCHES "ad", "abcd", "abcbcd" and DOES NOT MATCH "aed".
INCLUDE unit tests that VERIFY the regular expression "[0-9]+" MATCHES "123" and DOES NOT MATCH "abc".
