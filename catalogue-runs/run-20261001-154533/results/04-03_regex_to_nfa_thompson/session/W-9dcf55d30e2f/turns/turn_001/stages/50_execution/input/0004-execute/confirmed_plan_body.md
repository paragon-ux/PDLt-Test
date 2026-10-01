PARSE the supplied regular expression string.
TOKENIZE the expression into literals, operators, character classes, dot, and grouping symbols.
CONVERT the token sequence to postfix notation to resolve operator precedence.
FOR each token in postfix order:
    IF token is a literal, character class, or dot THEN
        BUILD a basic NFA fragment with a start state, a transition labeled with the token, and an accept state.
    ELSE IF token is concatenation THEN
        COMBINE the two topmost NFA fragments by connecting the accept state of the first to the start state of the second with an epsilon transition.
    ELSE IF token is alternation (|) THEN
        CREATE a new start state and a new accept state.
        ADD epsilon transitions from the new start to the start states of the two fragments.
        ADD epsilon transitions from the accept states of the two fragments to the new accept.
    ELSE IF token is Kleene star (*) THEN
        CREATE a new start state and a new accept state.
        ADD epsilon transition from the new start to the fragment start and to the new accept.
        ADD epsilon transition from the fragment accept back to the fragment start and to the new accept.
    ELSE IF token is plus (+) THEN
        APPLY the Kleene star construction to a copy of the fragment and then concatenate the original fragment with the starred fragment.
    ELSE IF token is optional (?) THEN
        CREATE a new start state and a new accept state.
        ADD epsilon transition from the new start to the fragment start and to the new accept.
        ADD epsilon transition from the fragment accept to the new accept.
END FOR
ENSURE that all transitions in the assembled NFA are epsilon or labeled with the appropriate character, character class, or dot, with no backtracking logic.
IMPLEMENT a simulation routine that computes the epsilon‑closure of the start state, then iterates over each input character:
    UPDATE the active state set by following transitions that match the current character (including dot and character class matches).
    RECOMPUTE the epsilon‑closure of the resulting state set.
AFTER processing the input string, DETERMINE acceptance by checking whether the accept state is within the active state set.
DESIGN unit tests for the regular expression "a(b|c)*d":
    DEFINE positive test strings "ad", "abcd", "abcbcd".
    DEFINE negative test string "aed".
    FOR each test string:
        CONSTRUCT the NFA using the implementation steps.
        SIMULATE the NFA on the test string.
        VERIFY that positive strings are accepted and the negative string is rejected.
DESIGN unit tests for the regular expression "[0-9]+":
    DEFINE positive test string "123".
    DEFINE negative test string "abc".
    FOR each test string:
        CONSTRUCT the NFA.
        SIMULATE the NFA.
        VERIFY that the positive string is accepted and the negative string is rejected.
EXECUTE all defined unit tests and REPORT the outcomes.
