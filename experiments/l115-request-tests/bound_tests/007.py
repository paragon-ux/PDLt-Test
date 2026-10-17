import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_pattern_a_b_c_star_d_matches_ad(self):
        self.assertTrue(nfa_match("a(b|c)*d", "ad"))
        
    def test_pattern_a_b_c_star_d_matches_abcd(self):
        self.assertTrue(nfa_match("a(b|c)*d", "abcd"))
        
    def test_pattern_a_b_c_star_d_matches_abcbcd(self):
        self.assertTrue(nfa_match("a(b|c)*d", "abcbcd"))
        
    def test_pattern_a_b_c_star_d_does_not_match_aed(self):
        self.assertFalse(nfa_match("a(b|c)*d", "aed"))
        
    def test_pattern_0_9_plus_matches_123(self):
        self.assertTrue(nfa_match("[0-9]+", "123"))
        
    def test_pattern_0_9_plus_does_not_match_abc(self):
        self.assertFalse(nfa_match("[0-9]+", "abc"))

def run_tests():
    unittest.main()

if __name__ == '__main__':
    run_tests()
