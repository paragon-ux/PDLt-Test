import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_a_b_c_star_d_matches_ad(self):
        regex = "a(b|c)*d"
        tokens = tokenize(regex)
        tokens = insert_concat(tokens)
        postfix = to_postfix(tokens)
        nfa = build_nfa(postfix)
        self.assertTrue(matches(nfa.start, "ad"), "Should match 'ad'")
    
    def test_a_b_c_star_d_matches_abcd(self):
        regex = "a(b|c)*d"
        tokens = tokenize(regex)
        tokens = insert_concat(tokens)
        postfix = to_postfix(tokens)
        nfa = build_nfa(postfix)
        self.assertTrue(matches(nfa.start, "abcd"), "Should match 'abcd'")
    
    def test_a_b_c_star_d_matches_abcbcd(self):
        regex = "a(b|c)*d"
        tokens = tokenize(regex)
        tokens = insert_concat(tokens)
        postfix = to_postfix(tokens)
        nfa = build_nfa(postfix)
        self.assertTrue(matches(nfa.start, "abcbcd"), "Should match 'abcbcd'")
    
    def test_a_b_c_star_d_not_match_aed(self):
        regex = "a(b|c)*d"
        tokens = tokenize(regex)
        tokens = insert_concat(tokens)
        postfix = to_postfix(tokens)
        nfa = build_nfa(postfix)
        self.assertFalse(matches(nfa.start, "aed"), "Should not match 'aed'")
    
    def test_0_9_plus_matches_123(self):
        regex = "[0-9]+"
        tokens = tokenize(regex)
        tokens = insert_concat(tokens)
        postfix = to_postfix(tokens)
        nfa = build_nfa(postfix)
        self.assertTrue(matches(nfa.start, "123"), "Should match '123'")
    
    def test_0_9_plus_not_match_abc(self):
        regex = "[0-9]+"
        tokens = tokenize(regex)
        tokens = insert_concat(tokens)
        postfix = to_postfix(tokens)
        nfa = build_nfa(postfix)
        self.assertFalse(matches(nfa.start, "abc"), "Should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
