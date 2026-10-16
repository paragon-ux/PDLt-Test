import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_concatenation_basic(self):
        self.assertTrue(match_regex("ab", "ab"))
        self.assertFalse(match_regex("ab", "ac"))
        self.assertFalse(match_regex("ab", "a"))
    
    def test_alternation_basic(self):
        self.assertTrue(match_regex("a|b", "a"))
        self.assertTrue(match_regex("a|b", "b"))
        self.assertFalse(match_regex("a|b", "c"))
    
    def test_kleene_star(self):
        self.assertTrue(match_regex("a*", ""))
        self.assertTrue(match_regex("a*", "a"))
        self.assertTrue(match_regex("a*", "aaaa"))
        self.assertFalse(match_regex("a*", "b"))
    
    def test_plus_operator(self):
        self.assertTrue(match_regex("a+", "a"))
        self.assertTrue(match_regex("a+", "aaa"))
        self.assertFalse(match_regex("a+", ""))
        self.assertFalse(match_regex("a+", "b"))
    
    def test_optional_operator(self):
        self.assertTrue(match_regex("a?", ""))
        self.assertTrue(match_regex("a?", "a"))
        self.assertFalse(match_regex("a?", "aa"))
    
    def test_dot_matches_any(self):
        self.assertTrue(match_regex("a.c", "abc"))
        self.assertTrue(match_regex("a.c", "a#c"))
        self.assertFalse(match_regex("a.c", "ac"))
    
    def test_character_class(self):
        self.assertTrue(match_regex("[a-z]", "m"))
        self.assertFalse(match_regex("[a-z]", "M"))
        self.assertFalse(match_regex("[a-z]", "1"))
    
    def test_given_example_1(self):
        pattern = "a(b|c)*d"
        self.assertTrue(match_regex(pattern, "ad"))
        self.assertTrue(match_regex(pattern, "abcd"))
        self.assertTrue(match_regex(pattern, "abcbcd"))
        self.assertFalse(match_regex(pattern, "aed"))
    
    def test_given_example_2(self):
        pattern = "[0-9]+"
        self.assertTrue(match_regex(pattern, "123"))
        self.assertFalse(match_regex(pattern, "abc"))
    
    def test_grouping(self):
        self.assertTrue(match_regex("(ab)*", ""))
        self.assertTrue(match_regex("(ab)*", "ab"))
        self.assertTrue(match_regex("(ab)*", "abab"))
        self.assertFalse(match_regex("(ab)*", "a"))
    
    def test_complex_pattern(self):
        pattern = "[a-z]+@[a-z]+\\.[a-z]+"
        self.assertTrue(match_regex(pattern, "test@example.com"))
        self.assertFalse(match_regex(pattern, "test@example"))

if __name__ == "__main__":
    unittest.main()
