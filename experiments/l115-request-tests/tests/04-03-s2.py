import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_regex_to_nfa_interface(self):
        """Test that regex_to_nfa function exists and returns an NFA object"""
        self.assertTrue(callable(regex_to_nfa), "regex_to_nfa should be a callable function")
        nfa = regex_to_nfa("a")
        self.assertTrue(hasattr(nfa, 'matches'), "NFA should have a matches method")
    
    def test_concatenation_match(self):
        """Test concatenation: 'a(b|c)*d' matches 'ad'"""
        nfa = regex_to_nfa("a(b|c)*d")
        self.assertTrue(nfa.matches("ad"), "Should match 'ad'")
    
    def test_concatenation_with_repetition(self):
        """Test concatenation with repetition: 'a(b|c)*d' matches 'abcd'"""
        nfa = regex_to_nfa("a(b|c)*d")
        self.assertTrue(nfa.matches("abcd"), "Should match 'abcd'")
    
    def test_concatenation_with_multiple_repetition(self):
        """Test concatenation with multiple repetitions: 'a(b|c)*d' matches 'abcbcd'"""
        nfa = regex_to_nfa("a(b|c)*d")
        self.assertTrue(nfa.matches("abcbcd"), "Should match 'abcbcd'")
    
    def test_concatenation_non_match(self):
        """Test concatenation non-match: 'a(b|c)*d' does not match 'aed'"""
        nfa = regex_to_nfa("a(b|c)*d")
        self.assertFalse(nfa.matches("aed"), "Should not match 'aed'")
    
    def test_character_class_match(self):
        """Test character class: '[0-9]+' matches '123'"""
        nfa = regex_to_nfa("[0-9]+")
        self.assertTrue(nfa.matches("123"), "Should match '123'")
    
    def test_character_class_non_match(self):
        """Test character class non-match: '[0-9]+' does not match 'abc'"""
        nfa = regex_to_nfa("[0-9]+")
        self.assertFalse(nfa.matches("abc"), "Should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
