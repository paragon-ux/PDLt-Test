import unittest

class TestRegexMatching(unittest.TestCase):
    
    def test_pattern_a_b_c_star_d_matches_ad(self):
        regex = Regex("a(b|c)*d")
        self.assertTrue(regex.match("ad"), "Pattern should match 'ad'")
    
    def test_pattern_a_b_c_star_d_matches_abcd(self):
        regex = Regex("a(b|c)*d")
        self.assertTrue(regex.match("abcd"), "Pattern should match 'abcd'")
    
    def test_pattern_a_b_c_star_d_matches_abcbcd(self):
        regex = Regex("a(b|c)*d")
        self.assertTrue(regex.match("abcbcd"), "Pattern should match 'abcbcd'")
    
    def test_pattern_a_b_c_star_d_does_not_match_aed(self):
        regex = Regex("a(b|c)*d")
        self.assertFalse(regex.match("aed"), "Pattern should not match 'aed'")
    
    def test_pattern_0_9_plus_matches_123(self):
        regex = Regex("[0-9]+")
        self.assertTrue(regex.match("123"), "Pattern should match '123'")
    
    def test_pattern_0_9_plus_does_not_match_abc(self):
        regex = Regex("[0-9]+")
        self.assertFalse(regex.match("abc"), "Pattern should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
