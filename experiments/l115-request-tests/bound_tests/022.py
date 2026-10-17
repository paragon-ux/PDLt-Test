import unittest

class TestThompsonConstruction(unittest.TestCase):
    def test_compile_regex_returns_nfa(self):
        start, accept = compile_regex("a")
        self.assertIsNotNone(start)
        self.assertIsNotNone(accept)
        self.assertIsInstance(start, State)
        self.assertIsInstance(accept, State)

    def test_nfa_simulator_basic_match(self):
        start, accept = compile_regex("a")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("a"))
        self.assertFalse(sim.matches("b"))

    def test_concatenation(self):
        start, accept = compile_regex("ab")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("ab"))
        self.assertFalse(sim.matches("a"))
        self.assertFalse(sim.matches("b"))
        self.assertFalse(sim.matches("abc"))

    def test_alternation(self):
        start, accept = compile_regex("a|b")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("a"))
        self.assertTrue(sim.matches("b"))
        self.assertFalse(sim.matches("c"))

    def test_kleene_star(self):
        start, accept = compile_regex("a*")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches(""))
        self.assertTrue(sim.matches("a"))
        self.assertTrue(sim.matches("aa"))
        self.assertTrue(sim.matches("aaa"))
        self.assertFalse(sim.matches("b"))

    def test_plus(self):
        start, accept = compile_regex("a+")
        sim = NFASimulator(start, accept)
        self.assertFalse(sim.matches(""))
        self.assertTrue(sim.matches("a"))
        self.assertTrue(sim.matches("aa"))
        self.assertFalse(sim.matches("b"))

    def test_optional(self):
        start, accept = compile_regex("a?")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches(""))
        self.assertTrue(sim.matches("a"))
        self.assertFalse(sim.matches("aa"))
        self.assertFalse(sim.matches("b"))

    def test_dot_matches_any_character(self):
        start, accept = compile_regex("a.c")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("abc"))
        self.assertTrue(sim.matches("a c"))
        self.assertTrue(sim.matches("a1c"))
        self.assertFalse(sim.matches("ac"))

    def test_character_class_basic(self):
        start, accept = compile_regex("[abc]")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("a"))
        self.assertTrue(sim.matches("b"))
        self.assertTrue(sim.matches("c"))
        self.assertFalse(sim.matches("d"))

    def test_character_class_range(self):
        start, accept = compile_regex("[0-9]")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("0"))
        self.assertTrue(sim.matches("5"))
        self.assertTrue(sim.matches("9"))
        self.assertFalse(sim.matches("a"))

    def test_grouping(self):
        start, accept = compile_regex("(a|b)c")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("ac"))
        self.assertTrue(sim.matches("bc"))
        self.assertFalse(sim.matches("cc"))

    def test_complex_pattern_example1(self):
        start, accept = compile_regex("a(b|c)*d")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("ad"))
        self.assertTrue(sim.matches("abcd"))
        self.assertTrue(sim.matches("abcbcd"))
        self.assertFalse(sim.matches("aed"))

    def test_complex_pattern_example2(self):
        start, accept = compile_regex("[0-9]+")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches("123"))
        self.assertFalse(sim.matches("abc"))

    def test_empty_string_match(self):
        start, accept = compile_regex("")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches(""))

    def test_nested_operators(self):
        start, accept = compile_regex("(a|b)*c?")
        sim = NFASimulator(start, accept)
        self.assertTrue(sim.matches(""))
        self.assertTrue(sim.matches("c"))
        self.assertTrue(sim.matches("ac"))
        self.assertTrue(sim.matches("bc"))
        self.assertTrue(sim.matches("aac"))
        self.assertFalse(sim.matches("d"))

if __name__ == '__main__':
    unittest.main()
