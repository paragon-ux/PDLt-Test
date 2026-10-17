import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_example_1_matches(self):
        """Test that 'a(b|c)*d' matches valid strings"""
        pattern = "a(b|c)*d"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, "ad"), "Should match 'ad'")
        self.assertTrue(matches(fragment, "abcd"), "Should match 'abcd'")
        self.assertTrue(matches(fragment, "abcbcd"), "Should match 'abcbcd'")
    
    def test_example_1_non_match(self):
        """Test that 'a(b|c)*d' rejects invalid strings"""
        pattern = "a(b|c)*d"
        fragment = compile_regex(pattern)
        
        self.assertFalse(matches(fragment, "aed"), "Should not match 'aed'")
    
    def test_example_2_matches(self):
        """Test that '[0-9]+' matches valid strings"""
        pattern = "[0-9]+"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, "123"), "Should match '123'")
    
    def test_example_2_non_match(self):
        """Test that '[0-9]+' rejects invalid strings"""
        pattern = "[0-9]+"
        fragment = compile_regex(pattern)
        
        self.assertFalse(matches(fragment, "abc"), "Should not match 'abc'")
    
    def test_concatenation(self):
        """Test concatenation operation"""
        pattern = "ab"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, "ab"), "Should match 'ab'")
        self.assertFalse(matches(fragment, "a"), "Should not match 'a'")
        self.assertFalse(matches(fragment, "b"), "Should not match 'b'")
        self.assertFalse(matches(fragment, "ac"), "Should not match 'ac'")
    
    def test_alternation(self):
        """Test alternation operation"""
        pattern = "a|b"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, "a"), "Should match 'a'")
        self.assertTrue(matches(fragment, "b"), "Should match 'b'")
        self.assertFalse(matches(fragment, "c"), "Should not match 'c'")
    
    def test_kleene_star(self):
        """Test Kleene star operation"""
        pattern = "a*"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, ""), "Should match empty string")
        self.assertTrue(matches(fragment, "a"), "Should match 'a'")
        self.assertTrue(matches(fragment, "aaa"), "Should match 'aaa'")
    
    def test_plus(self):
        """Test plus operation"""
        pattern = "a+"
        fragment = compile_regex(pattern)
        
        self.assertFalse(matches(fragment, ""), "Should not match empty string")
        self.assertTrue(matches(fragment, "a"), "Should match 'a'")
        self.assertTrue(matches(fragment, "aaa"), "Should match 'aaa'")
    
    def test_optional(self):
        """Test optional operation"""
        pattern = "a?"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, ""), "Should match empty string")
        self.assertTrue(matches(fragment, "a"), "Should match 'a'")
        self.assertFalse(matches(fragment, "aa"), "Should not match 'aa'")
    
    def test_character_class(self):
        """Test character class operation"""
        pattern = "[a-z]"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, "a"), "Should match 'a'")
        self.assertTrue(matches(fragment, "z"), "Should match 'z'")
        self.assertFalse(matches(fragment, "0"), "Should not match '0'")
        self.assertFalse(matches(fragment, "A"), "Should not match 'A'")
    
    def test_dot(self):
        """Test dot operation"""
        pattern = "."
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, "a"), "Should match 'a'")
        self.assertTrue(matches(fragment, "z"), "Should match 'z'")
        self.assertTrue(matches(fragment, "0"), "Should match '0'")
        self.assertFalse(matches(fragment, ""), "Should not match empty string")
    
    def test_grouping(self):
        """Test grouping with parentheses"""
        pattern = "(a|b)c"
        fragment = compile_regex(pattern)
        
        self.assertTrue(matches(fragment, "ac"), "Should match 'ac'")
        self.assertTrue(matches(fragment, "bc"), "Should match 'bc'")
        self.assertFalse(matches(fragment, "ab"), "Should not match 'ab'")
        self.assertFalse(matches(fragment, "c"), "Should not match 'c'")

if __name__ == '__main__':
    unittest.main()
