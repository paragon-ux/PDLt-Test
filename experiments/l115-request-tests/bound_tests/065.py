import unittest

class TestRegexMatching(unittest.TestCase):
    
    def test_concatenation_basic(self):
        self.assertTrue(matches("ab", "ab"))
        self.assertFalse(matches("ab", "ac"))
    
    def test_alternation(self):
        self.assertTrue(matches("a|b", "a"))
        self.assertTrue(matches("a|b", "b"))
        self.assertFalse(matches("a|b", "c"))
    
    def test_kleene_star(self):
        self.assertTrue(matches("a*", ""))
        self.assertTrue(matches("a*", "a"))
        self.assertTrue(matches("a*", "aaa"))
        self.assertFalse(matches("a*", "b"))
    
    def test_plus(self):
        self.assertTrue(matches("a+", "a"))
        self.assertTrue(matches("a+", "aaa"))
        self.assertFalse(matches("a+", ""))
        self.assertFalse(matches("a+", "b"))
    
    def test_optional(self):
        self.assertTrue(matches("a?", ""))
        self.assertTrue(matches("a?", "a"))
        self.assertFalse(matches("a?", "aa"))
    
    def test_character_class(self):
        self.assertTrue(matches("[a-z]", "a"))
        self.assertTrue(matches("[a-z]", "z"))
        self.assertFalse(matches("[a-z]", "A"))
        self.assertFalse(matches("[a-z]", "1"))
    
    def test_dot(self):
        self.assertTrue(matches(".", "a"))
        self.assertTrue(matches(".", "1"))
        self.assertFalse(matches(".", ""))
    
    def test_grouping(self):
        self.assertTrue(matches("(a|b)c", "ac"))
        self.assertTrue(matches("(a|b)c", "bc"))
        self.assertFalse(matches("(a|b)c", "cc"))
    
    def test_complex_pattern_example1(self):
        pattern = "a(b|c)*d"
        self.assertTrue(matches(pattern, "ad"))
        self.assertTrue(matches(pattern, "abcd"))
        self.assertTrue(matches(pattern, "abcbcd"))
        self.assertFalse(matches(pattern, "aed"))
    
    def test_character_class_plus_example2(self):
        pattern = "[0-9]+"
        self.assertTrue(matches(pattern, "123"))
        self.assertFalse(matches(pattern, "abc"))
    
    def test_nested_operations(self):
        self.assertTrue(matches("(ab)*c", "c"))
        self.assertTrue(matches("(ab)*c", "abc"))
        self.assertTrue(matches("(ab)*c", "ababc"))
        self.assertFalse(matches("(ab)*c", "abac"))
    
    def test_mixed_operators(self):
        self.assertTrue(matches("a(b|c)*d?", "ad"))
        self.assertTrue(matches("a(b|c)*d?", "abcd"))
        self.assertTrue(matches("a(b|c)*d?", "abcbcd"))
        self.assertTrue(matches("a(b|c)*d?", "abcbcd"))
        self.assertFalse(matches("a(b|c)*d?", "aed"))
    
    def test_empty_string_matching(self):
        self.assertTrue(matches("", ""))
        self.assertFalse(matches("a", ""))
        self.assertTrue(matches("a*", ""))
        self.assertTrue(matches("a?", ""))
        self.assertFalse(matches("a+", ""))
