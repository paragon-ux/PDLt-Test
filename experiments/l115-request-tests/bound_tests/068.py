import unittest

class TestThompsonConstruction(unittest.TestCase):
    def test_matches_a_b_c_star_d_ad(self):
        self.assertTrue(matches("a(b|c)*d", "ad"), "Should match 'ad'")
    
    def test_matches_a_b_c_star_d_abcd(self):
        self.assertTrue(matches("a(b|c)*d", "abcd"), "Should match 'abcd'")
    
    def test_matches_a_b_c_star_d_abcbcd(self):
        self.assertTrue(matches("a(b|c)*d", "abcbcd"), "Should match 'abcbcd'")
    
    def test_does_not_match_a_b_c_star_d_aed(self):
        self.assertFalse(matches("a(b|c)*d", "aed"), "Should not match 'aed'")
    
    def test_matches_0_9_plus_123(self):
        self.assertTrue(matches("[0-9]+", "123"), "Should match '123'")
    
    def test_does_not_match_0_9_plus_abc(self):
        self.assertFalse(matches("[0-9]+", "abc"), "Should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
