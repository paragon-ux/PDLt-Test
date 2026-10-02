IMPLEMENT a Python module that converts a regular expression to an NFA using Thompson's construction.
SUPPORT concatenation, alternation '|', Kleene star '*', plus '+', optional '?', character classes '[a-z]', dot '.' and grouping with parentheses.
BUILD the NFA using epsilon transitions only; DO NOT use backtracking.
MATCH strings using simultaneous NFA simulation that tracks the set of active states.
INCLUDE tests: the regular expression 'a(b|c)*d' must match 'ad', 'abcd', and 'abcbcd', and must NOT match 'aed'; the regular expression '[0-9]+' must match '123' and must NOT match 'abc'.
DELIVER the solution as a single Python file containing the implementation and the tests.
