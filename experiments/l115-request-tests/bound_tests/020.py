import unittest

class TestRegexNFA(unittest.TestCase):
    
    def test_a_b_c_star_d_matches_ad(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.match("ad"), "Pattern should match 'ad'")
    
    def test_a_b_c_star_d_matches_abcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.match("abcd"), "Pattern should match 'abcd'")
    
    def test_a_b_c_star_d_matches_abcbcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.match("abcbcd"), "Pattern should match 'abcbcd'")
    
    def test_a_b_c_star_d_not_match_aed(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertFalse(nfa.match("aed"), "Pattern should not match 'aed'")
    
    def test_0_9_plus_matches_123(self):
        nfa = compile_regex("[0-9]+")
        self.assertTrue(nfa.match("123"), "Pattern should match '123'")
    
    def test_0_9_plus_not_match_abc(self):
        nfa = compile_regex("[0-9]+")
        self.assertFalse(nfa.match("abc"), "Pattern should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
