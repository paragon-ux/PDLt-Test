import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_pattern_a_b_or_c_star_d_matches_ad(self):
        nfa = compile_pattern("a(b|c)*d")
        self.assertTrue(matches(nfa, "ad"), "Pattern should match 'ad'")
    
    def test_pattern_a_b_or_c_star_d_matches_abcd(self):
        nfa = compile_pattern("a(b|c)*d")
        self.assertTrue(matches(nfa, "abcd"), "Pattern should match 'abcd'")
    
    def test_pattern_a_b_or_c_star_d_matches_abcbcd(self):
        nfa = compile_pattern("a(b|c)*d")
        self.assertTrue(matches(nfa, "abcbcd"), "Pattern should match 'abcbcd'")
    
    def test_pattern_a_b_or_c_star_d_not_match_aed(self):
        nfa = compile_pattern("a(b|c)*d")
        self.assertFalse(matches(nfa, "aed"), "Pattern should not match 'aed'")
    
    def test_pattern_0_9_plus_matches_123(self):
        nfa = compile_pattern("[0-9]+")
        self.assertTrue(matches(nfa, "123"), "Pattern should match '123'")
    
    def test_pattern_0_9_plus_not_match_abc(self):
        nfa = compile_pattern("[0-9]+")
        self.assertFalse(matches(nfa, "abc"), "Pattern should not match 'abc'")

def run_tests():
    unittest.main(argv=[''], exit=False, verbosity=2)

if __name__ == '__main__':
    run_tests()
