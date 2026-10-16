import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_pattern_a_b_c_star_d_matches_ad(self):
        pattern = "a(b|c)*d"
        self.assertTrue(match(pattern, "ad"), "Pattern should match 'ad'")
    
    def test_pattern_a_b_c_star_d_matches_abcd(self):
        pattern = "a(b|c)*d"
        self.assertTrue(match(pattern, "abcd"), "Pattern should match 'abcd'")
    
    def test_pattern_a_b_c_star_d_matches_abcbcd(self):
        pattern = "a(b|c)*d"
        self.assertTrue(match(pattern, "abcbcd"), "Pattern should match 'abcbcd'")
    
    def test_pattern_a_b_c_star_d_does_not_match_aed(self):
        pattern = "a(b|c)*d"
        self.assertFalse(match(pattern, "aed"), "Pattern should not match 'aed'")
    
    def test_pattern_0_9_plus_matches_123(self):
        pattern = "[0-9]+"
        self.assertTrue(match(pattern, "123"), "Pattern should match '123'")
    
    def test_pattern_0_9_plus_does_not_match_abc(self):
        pattern = "[0-9]+"
        self.assertFalse(match(pattern, "abc"), "Pattern should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
