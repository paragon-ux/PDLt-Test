PARSE the regular expression string into an abstract syntax tree supporting concatenation, alternation '|', Kleene star '*', plus '+', optional '?', character classes, dot '.' and grouping parentheses.
CONSTRUCT an NFA fragment for each syntax‑tree node using Thompson's construction with epsilon transitions only.
  FOR literal characters, CREATE a two‑state fragment with a transition on the character.
  FOR concatenation, CONNECT the accept state of the first fragment to the start state of the second via an epsilon transition.
  FOR alternation, CREATE a new start state with epsilon transitions to the start states of the alternatives and a new accept state with epsilon transitions from the alternatives' accept states.
  FOR Kleene star, CREATE a new start and accept state with epsilon loops to the sub‑fragment and from the sub‑fragment back to the start.
  FOR plus, REUSE the Kleene star construction but ENSURE at least one traversal of the sub‑fragment.
  FOR optional, ADD an epsilon transition that bypasses the sub‑fragment.
  FOR character classes and dot, CREATE transitions that match any character in the specified set or any character respectively.
MERGE the fragments according to the syntax‑tree structure to obtain a single start state and a single accept state.
COMPUTE epsilon‑closure for any set of NFA states.
SIMULATE the NFA by iteratively updating the active state set for each input character using transition functions and epsilon‑closure.
EVALUATE a match by checking whether the accept state is present in the final active state set after processing the entire input string.
WRITE unit tests for the pattern 'a(b|c)*d' asserting that 'ad', 'abcd', and 'abcbcd' match and that 'aed' does not match.
WRITE unit tests for the pattern '[0-9]+' asserting that '123' matches and that 'abc' does not match.
PACKAGE the implementation and tests into a single Python file, INCLUDING a `if __name__ == '__main__':` block to run the tests.
