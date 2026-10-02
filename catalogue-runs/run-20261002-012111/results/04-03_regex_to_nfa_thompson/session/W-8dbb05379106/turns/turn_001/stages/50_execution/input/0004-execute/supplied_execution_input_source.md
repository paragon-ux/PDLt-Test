Implement Thompson's construction in Python: convert a regular expression to an NFA, then use the NFA to match strings.
1. Support: concatenation, alternation (|), Kleene star (*), plus (+), optional (?), character classes ([a-z]), dot (.), and grouping with parentheses.
2. Build the NFA using Thompson's construction (epsilon transitions, no backtracking).
3. Match using the simultaneous NFA simulation (track set of active states).
4. Include tests: "a(b|c)*d" matches "ad", "abcd", "abcbcd" but not "aed"; "[0-9]+" matches "123" but not "abc".
