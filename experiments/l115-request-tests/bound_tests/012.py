import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_a_b_c_star_d_matches_ad(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("ad"), "Should match 'ad'")
    
    def test_a_b_c_star_d_matches_abcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("abcd"), "Should match 'abcd'")
    
    def test_a_b_c_star_d_matches_abcbcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("abcbcd"), "Should match 'abcbcd'")
    
    def test_a_b_c_star_d_does_not_match_aed(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertFalse(nfa.matches("aed"), "Should not match 'aed'")
    
    def test_char_class_0_9_plus_matches_123(self):
        nfa = compile_regex("[0-9]+")
        self.assertTrue(nfa.matches("123"), "Should match '123'")
    
    def test_char_class_0_9_plus_does_not_match_abc(self):
        nfa = compile_regex("[0-9]+")
        self.assertFalse(nfa.matches("abc"), "Should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
