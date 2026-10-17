import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_pattern_a_b_c_star_d_matches_ad(self):
        self.assertTrue(matches("a(b|c)*d", "ad"), "Pattern should match 'ad'")
    
    def test_pattern_a_b_c_star_d_matches_abcd(self):
        self.assertTrue(matches("a(b|c)*d", "abcd"), "Pattern should match 'abcd'")
    
    def test_pattern_a_b_c_star_d_matches_abcbcd(self):
        self.assertTrue(matches("a(b|c)*d", "abcbcd"), "Pattern should match 'abcbcd'")
    
    def test_pattern_a_b_c_star_d_does_not_match_aed(self):
        self.assertFalse(matches("a(b|c)*d", "aed"), "Pattern should not match 'aed'")
    
    def test_pattern_0_9_plus_matches_123(self):
        self.assertTrue(matches("[0-9]+", "123"), "Pattern should match '123'")
    
    def test_pattern_0_9_plus_does_not_match_abc(self):
        self.assertFalse(matches("[0-9]+", "abc"), "Pattern should not match 'abc'")

def run_tests():
    unittest.main()

if __name__ == '__main__':
    run_tests()
