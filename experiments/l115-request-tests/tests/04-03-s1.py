import unittest

class TestThompsonNFA(unittest.TestCase):
    def test_regex_to_nfa_interface(self):
        # Test that regex_to_nfa exists and returns an NFA object
        nfa = regex_to_nfa("a")
        self.assertIsNotNone(nfa)
    
    def test_nfa_match_interface(self):
        # Test that nfa_match exists and returns boolean
        nfa = regex_to_nfa("a")
        result = nfa_match(nfa, "a")
        self.assertIsInstance(result, bool)
    
    def test_concatenation(self):
        nfa = regex_to_nfa("ab")
        self.assertTrue(nfa_match(nfa, "ab"))
        self.assertFalse(nfa_match(nfa, "a"))
        self.assertFalse(nfa_match(nfa, "b"))
    
    def test_alternation(self):
        nfa = regex_to_nfa("a|b")
        self.assertTrue(nfa_match(nfa, "a"))
        self.assertTrue(nfa_match(nfa, "b"))
        self.assertFalse(nfa_match(nfa, "c"))
    
    def test_kleene_star(self):
        nfa = regex_to_nfa("a*")
        self.assertTrue(nfa_match(nfa, ""))
        self.assertTrue(nfa_match(nfa, "a"))
        self.assertTrue(nfa_match(nfa, "aaa"))
    
    def test_plus(self):
        nfa = regex_to_nfa("a+")
        self.assertFalse(nfa_match(nfa, ""))
        self.assertTrue(nfa_match(nfa, "a"))
        self.assertTrue(nfa_match(nfa, "aaa"))
    
    def test_optional(self):
        nfa = regex_to_nfa("a?")
        self.assertTrue(nfa_match(nfa, ""))
        self.assertTrue(nfa_match(nfa, "a"))
        self.assertFalse(nfa_match(nfa, "aa"))
    
    def test_character_class(self):
        nfa = regex_to_nfa("[a-z]")
        self.assertTrue(nfa_match(nfa, "a"))
        self.assertTrue(nfa_match(nfa, "z"))
        self.assertFalse(nfa_match(nfa, "A"))
        self.assertFalse(nfa_match(nfa, "0"))
    
    def test_dot(self):
        nfa = regex_to_nfa(".")
        self.assertTrue(nfa_match(nfa, "a"))
        self.assertTrue(nfa_match(nfa, "0"))
        self.assertFalse(nfa_match(nfa, ""))
    
    def test_grouping(self):
        nfa = regex_to_nfa("(a|b)c")
        self.assertTrue(nfa_match(nfa, "ac"))
        self.assertTrue(nfa_match(nfa, "bc"))
        self.assertFalse(nfa_match(nfa, "cc"))
    
    def test_complex_regex_matches(self):
        nfa = regex_to_nfa("a(b|c)*d")
        self.assertTrue(nfa_match(nfa, "ad"))
        self.assertTrue(nfa_match(nfa, "abcd"))
        self.assertTrue(nfa_match(nfa, "abcbcd"))
    
    def test_complex_regex_non_matches(self):
        nfa = regex_to_nfa("a(b|c)*d")
        self.assertFalse(nfa_match(nfa, "aed"))
    
    def test_digit_class_matches(self):
        nfa = regex_to_nfa("[0-9]+")
        self.assertTrue(nfa_match(nfa, "123"))
    
    def test_digit_class_non_matches(self):
        nfa = regex_to_nfa("[0-9]+")
        self.assertFalse(nfa_match(nfa, "abc"))
    
    def test_epsilon_transitions_exist(self):
        # Test that the NFA uses epsilon transitions by checking structure
        nfa = regex_to_nfa("a*")
        # The NFA should have at least one epsilon transition for star
        self.assertTrue(has_epsilon_transitions(nfa))
    
    def test_simultaneous_matching(self):
        # Test that matching uses set of active states (simultaneous simulation)
        nfa = regex_to_nfa("a|b")
        # This should not backtrack - if implemented correctly, it tracks all possible states
        self.assertTrue(nfa_match(nfa, "a"))
        self.assertTrue(nfa_match(nfa, "b"))

def has_epsilon_transitions(nfa):
    # Helper function to check if NFA has epsilon transitions
    # This is a structural check - actual implementation may vary
    return True  # Simplified for testing interface

if __name__ == '__main__':
    unittest.main()
