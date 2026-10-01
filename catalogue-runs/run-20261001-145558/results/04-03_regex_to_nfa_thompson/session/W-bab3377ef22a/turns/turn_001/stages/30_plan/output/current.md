READ the specification for Thompson's construction in Python
DESIGN a converter that parses a regular expression into an abstract syntax tree supporting concatenation, alternation, Kleene star, plus, optional, character classes, dot, and grouping
IMPLEMENT the parser to produce the syntax tree
IMPLEMENT the NFA builder that traverses the syntax tree and constructs an NFA using epsilon transitions according to Thompson's construction without backtracking
IMPLEMENT a simultaneous NFA simulation that tracks the set of active states to match input strings
WRITE unit tests verifying that the NFA for "a(b|c)*d" matches "ad", "abcd", "abcbcd" and rejects "aed"
WRITE unit tests verifying that the NFA for "[0-9]+" matches "123" and rejects "abc"
