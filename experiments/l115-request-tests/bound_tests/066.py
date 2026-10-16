import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_basic_concatenation(self):
        nfa = compile_regex("ab")
        self.assertTrue(nfa.matches("ab"))
        self.assertFalse(nfa.matches("a"))
        self.assertFalse(nfa.matches("b"))
        self.assertFalse(nfa.matches("abc"))
    
    def test_alternation(self):
        nfa = compile_regex("a|b")
        self.assertTrue(nfa.matches("a"))
        self.assertTrue(nfa.matches("b"))
        self.assertFalse(nfa.matches("c"))
        self.assertFalse(nfa.matches("ab"))
    
    def test_kleene_star(self):
        nfa = compile_regex("a*")
        self.assertTrue(nfa.matches(""))
        self.assertTrue(nfa.matches("a"))
        self.assertTrue(nfa.matches("aa"))
        self.assertTrue(nfa.matches("aaa"))
        self.assertFalse(nfa.matches("b"))
    
    def test_plus(self):
        nfa = compile_regex("a+")
        self.assertTrue(nfa.matches("a"))
        self.assertTrue(nfa.matches("aa"))
        self.assertTrue(nfa.matches("aaa"))
        self.assertFalse(nfa.matches(""))
        self.assertFalse(nfa.matches("b"))
    
    def test_optional(self):
        nfa = compile_regex("a?")
        self.assertTrue(nfa.matches(""))
        self.assertTrue(nfa.matches("a"))
        self.assertFalse(nfa.matches("aa"))
        self.assertFalse(nfa.matches("b"))
    
    def test_character_class(self):
        nfa = compile_regex("[a-z]")
        self.assertTrue(nfa.matches("a"))
        self.assertTrue(nfa.matches("m"))
        self.assertTrue(nfa.matches("z"))
        self.assertFalse(nfa.matches("A"))
        self.assertFalse(nfa.matches("0"))
        self.assertFalse(nfa.matches(""))
    
    def test_dot(self):
        nfa = compile_regex("a.c")
        self.assertTrue(nfa.matches("abc"))
        self.assertTrue(nfa.matches("aXc"))
        self.assertFalse(nfa.matches("ac"))
        self.assertFalse(nfa.matches("abbc"))
    
    def test_grouping(self):
        nfa = compile_regex("(ab)*")
        self.assertTrue(nfa.matches(""))
        self.assertTrue(nfa.matches("ab"))
        self.assertTrue(nfa.matches("abab"))
        self.assertTrue(nfa.matches("ababab"))
        self.assertFalse(nfa.matches("a"))
        self.assertFalse(nfa.matches("ba"))
    
    def test_complex_pattern_1(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("ad"))
        self.assertTrue(nfa.matches("abcd"))
        self.assertTrue(nfa.matches("abcbcd"))
        self.assertFalse(nfa.matches("aed"))
        self.assertFalse(nfa.matches("abd"))
        self.assertFalse(nfa.matches("ab"))
    
    def test_complex_pattern_2(self):
        nfa = compile_regex("[0-9]+")
        self.assertTrue(nfa.matches("123"))
        self.assertTrue(nfa.matches("0"))
        self.assertTrue(nfa.matches("999"))
        self.assertFalse(nfa.matches("abc"))
        self.assertFalse(nfa.matches("1a2"))
        self.assertFalse(nfa.matches(""))
    
    def test_nested_groups(self):
        nfa = compile_regex("(a(b|c)*d)+")
        self.assertTrue(nfa.matches("ad"))
        self.assertTrue(nfa.matches("abcd"))
        self.assertTrue(nfa.matches("adabcd"))
        self.assertFalse(nfa.matches(""))
        self.assertFalse(nfa.matches("a"))
    
    def test_mixed_operators(self):
        nfa = compile_regex("a(b|c)*d?e")
        self.assertTrue(nfa.matches("ae"))
        self.assertTrue(nfa.matches("ade"))
        self.assertTrue(nfa.matches("abce"))
        self.assertFalse(nfa.matches("axde"))
        self.assertFalse(nfa.matches("ab"))
    
    def test_empty_pattern(self):
        nfa = compile_regex("")
        self.assertTrue(nfa.matches(""))
        self.assertFalse(nfa.matches("a"))
    
    def test_single_character(self):
        nfa = compile_regex("a")
        self.assertTrue(nfa.matches("a"))
        self.assertFalse(nfa.matches(""))
        self.assertFalse(nfa.matches("b"))
    
    def test_epsilon_closure_basic(self):
        nfa = compile_regex("a*")
        start_closure = nfa.epsilon_closure({nfa.start})
        self.assertIsInstance(start_closure, set)
        self.assertGreater(len(start_closure), 0)
    
    def test_move_basic(self):
        nfa = compile_regex("ab")
        start_closure = nfa.epsilon_closure({nfa.start})
        after_a = nfa.move(start_closure, 'a')
        self.assertIsInstance(after_a, set)
        after_b = nfa.move(after_a, 'b')
        self.assertIsInstance(after_b, set)

if __name__ == '__main__':
    unittest.main()
