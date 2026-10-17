import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_concat_basic(self):
        nfa1 = symbol('a')
        nfa2 = symbol('b')
        result = concat(nfa1, nfa2)
        self.assertIsNotNone(result)
        self.assertTrue(match(result, "ab"))
        self.assertFalse(match(result, "ba"))
        self.assertFalse(match(result, "a"))
        self.assertFalse(match(result, "b"))
    
    def test_alternate_basic(self):
        nfa1 = symbol('a')
        nfa2 = symbol('b')
        result = alternate(nfa1, nfa2)
        self.assertTrue(match(result, "a"))
        self.assertTrue(match(result, "b"))
        self.assertFalse(match(result, "ab"))
        self.assertFalse(match(result, "c"))
    
    def test_star_basic(self):
        nfa = symbol('a')
        result = star(nfa)
        self.assertTrue(match(result, ""))
        self.assertTrue(match(result, "a"))
        self.assertTrue(match(result, "aa"))
        self.assertTrue(match(result, "aaa"))
        self.assertFalse(match(result, "b"))
    
    def test_plus_basic(self):
        nfa = symbol('a')
        result = plus(nfa)
        self.assertFalse(match(result, ""))
        self.assertTrue(match(result, "a"))
        self.assertTrue(match(result, "aa"))
        self.assertTrue(match(result, "aaa"))
        self.assertFalse(match(result, "b"))
    
    def test_optional_basic(self):
        nfa = symbol('a')
        result = optional(nfa)
        self.assertTrue(match(result, ""))
        self.assertTrue(match(result, "a"))
        self.assertFalse(match(result, "aa"))
        self.assertFalse(match(result, "b"))
    
    def test_dot_matches_any_char(self):
        nfa = dot()
        self.assertTrue(match(nfa, "a"))
        self.assertTrue(match(nfa, "z"))
        self.assertTrue(match(nfa, "0"))
        self.assertFalse(match(nfa, ""))
    
    def test_char_class_matches_specified_chars(self):
        nfa = char_class("abc")
        self.assertTrue(match(nfa, "a"))
        self.assertTrue(match(nfa, "b"))
        self.assertTrue(match(nfa, "c"))
        self.assertFalse(match(nfa, "d"))
        self.assertFalse(match(nfa, ""))
    
    def test_pattern_a_b_c_star_d_matches_ad(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(match(nfa, "ad"))
    
    def test_pattern_a_b_c_star_d_matches_abcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(match(nfa, "abcd"))
    
    def test_pattern_a_b_c_star_d_matches_abcbcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(match(nfa, "abcbcd"))
    
    def test_pattern_a_b_c_star_d_not_match_aed(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertFalse(match(nfa, "aed"))
    
    def test_pattern_0_9_plus_matches_123(self):
        nfa = compile_regex("[0-9]+")
        self.assertTrue(match(nfa, "123"))
    
    def test_pattern_0_9_plus_not_match_abc(self):
        nfa = compile_regex("[0-9]+")
        self.assertFalse(match(nfa, "abc"))
    
    def test_epsilon_closure_empty_input(self):
        nfa = symbol('a')
        closure = epsilon_closure({nfa.start})
        self.assertIn(nfa.start, closure)
    
    def test_move_with_matching_char(self):
        nfa = symbol('a')
        next_states = move({nfa.start}, 'a')
        self.assertIn(nfa.accept, next_states)
    
    def test_move_with_non_matching_char(self):
        nfa = symbol('a')
        next_states = move({nfa.start}, 'b')
        self.assertEqual(len(next_states), 0)
    
    def test_tokenize_basic_pattern(self):
        tokens = tokenize("a|b")
        self.assertEqual(tokens, ['a', '|', 'b'])
    
    def test_to_postfix_basic_pattern(self):
        postfix = to_postfix("a|b")
        self.assertEqual(postfix, ['a', 'b', '|'])
    
    def test_build_nfa_from_postfix(self):
        postfix = ['a', 'b', '|']
        nfa = build_nfa(postfix)
        self.assertIsNotNone(nfa)
        self.assertTrue(match(nfa, "a"))
        self.assertTrue(match(nfa, "b"))
        self.assertFalse(match(nfa, "ab"))
    
    def test_compile_regex_returns_nfa(self):
        nfa = compile_regex("a")
        self.assertIsInstance(nfa, NFA)
        self.assertTrue(match(nfa, "a"))
        self.assertFalse(match(nfa, "b"))

if __name__ == '__main__':
    unittest.main()
