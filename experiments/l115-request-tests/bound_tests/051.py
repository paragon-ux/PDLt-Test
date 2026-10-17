import unittest

class TestNFAMatching(unittest.TestCase):
    
    def test_a_b_c_star_d_matches_ad(self):
        """Test that 'a(b|c)*d' matches 'ad'"""
        self.assertTrue(nfa_match("a(b|c)*d", "ad"), 
                       "Pattern 'a(b|c)*d' should match 'ad'")
    
    def test_a_b_c_star_d_matches_abcd(self):
        """Test that 'a(b|c)*d' matches 'abcd'"""
        self.assertTrue(nfa_match("a(b|c)*d", "abcd"), 
                       "Pattern 'a(b|c)*d' should match 'abcd'")
    
    def test_a_b_c_star_d_matches_abcbcd(self):
        """Test that 'a(b|c)*d' matches 'abcbcd'"""
        self.assertTrue(nfa_match("a(b|c)*d", "abcbcd"), 
                       "Pattern 'a(b|c)*d' should match 'abcbcd'")
    
    def test_a_b_c_star_d_does_not_match_aed(self):
        """Test that 'a(b|c)*d' does not match 'aed'"""
        self.assertFalse(nfa_match("a(b|c)*d", "aed"), 
                        "Pattern 'a(b|c)*d' should not match 'aed'")
    
    def test_char_class_0_9_plus_matches_123(self):
        """Test that '[0-9]+' matches '123'"""
        self.assertTrue(nfa_match("[0-9]+", "123"), 
                       "Pattern '[0-9]+' should match '123'")
    
    def test_char_class_0_9_plus_does_not_match_abc(self):
        """Test that '[0-9]+' does not match 'abc'"""
        self.assertFalse(nfa_match("[0-9]+", "abc"), 
                        "Pattern '[0-9]+' should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
