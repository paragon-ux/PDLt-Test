import unittest

class TestThompsonNFA(unittest.TestCase):
    
    def test_regex_a_b_c_star_d_matches_ad(self):
        nfa = NFA.from_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("ad"), "Should match 'ad'")
    
    def test_regex_a_b_c_star_d_matches_abcd(self):
        nfa = NFA.from_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("abcd"), "Should match 'abcd'")
    
    def test_regex_a_b_c_star_d_matches_abcbcd(self):
        nfa = NFA.from_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("abcbcd"), "Should match 'abcbcd'")
    
    def test_regex_a_b_c_star_d_does_not_match_aed(self):
        nfa = NFA.from_regex("a(b|c)*d")
        self.assertFalse(nfa.matches("aed"), "Should not match 'aed'")
    
    def test_regex_0_9_plus_matches_123(self):
        nfa = NFA.from_regex("[0-9]+")
        self.assertTrue(nfa.matches("123"), "Should match '123'")
    
    def test_regex_0_9_plus_does_not_match_abc(self):
        nfa = NFA.from_regex("[0-9]+")
        self.assertFalse(nfa.matches("abc"), "Should not match 'abc'")

def run_tests():
    unittest.main()

if __name__ == '__main__':
    run_tests()
