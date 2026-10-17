import unittest

class TestThompsonNFA(unittest.TestCase):
    
    def test_basic_concatenation(self):
        nfa = build_nfa("ab")
        self.assertTrue(nfa.matches("ab"), "Concatenation: 'ab' should match 'ab'")
        self.assertFalse(nfa.matches("a"), "Concatenation: 'ab' should not match 'a'")
        self.assertFalse(nfa.matches("ba"), "Concatenation: 'ab' should not match 'ba'")
    
    def test_alternation(self):
        nfa = build_nfa("a|b")
        self.assertTrue(nfa.matches("a"), "Alternation: 'a|b' should match 'a'")
        self.assertTrue(nfa.matches("b"), "Alternation: 'a|b' should match 'b'")
        self.assertFalse(nfa.matches("c"), "Alternation: 'a|b' should not match 'c'")
    
    def test_kleene_star(self):
        nfa = build_nfa("a*")
        self.assertTrue(nfa.matches(""), "Kleene star: 'a*' should match empty string")
        self.assertTrue(nfa.matches("a"), "Kleene star: 'a*' should match 'a'")
        self.assertTrue(nfa.matches("aaa"), "Kleene star: 'a*' should match 'aaa'")
        self.assertFalse(nfa.matches("b"), "Kleene star: 'a*' should not match 'b'")
    
    def test_plus(self):
        nfa = build_nfa("a+")
        self.assertFalse(nfa.matches(""), "Plus: 'a+' should not match empty string")
        self.assertTrue(nfa.matches("a"), "Plus: 'a+' should match 'a'")
        self.assertTrue(nfa.matches("aa"), "Plus: 'a+' should match 'aa'")
    
    def test_optional(self):
        nfa = build_nfa("a?")
        self.assertTrue(nfa.matches(""), "Optional: 'a?' should match empty string")
        self.assertTrue(nfa.matches("a"), "Optional: 'a?' should match 'a'")
        self.assertFalse(nfa.matches("aa"), "Optional: 'a?' should not match 'aa'")
    
    def test_character_class(self):
        nfa = build_nfa("[a-z]")
        self.assertTrue(nfa.matches("a"), "Char class: '[a-z]' should match 'a'")
        self.assertTrue(nfa.matches("z"), "Char class: '[a-z]' should match 'z'")
        self.assertFalse(nfa.matches("A"), "Char class: '[a-z]' should not match 'A'")
        self.assertFalse(nfa.matches("0"), "Char class: '[a-z]' should not match '0'")
    
    def test_dot_wildcard(self):
        nfa = build_nfa("a.c")
        self.assertTrue(nfa.matches("abc"), "Dot: 'a.c' should match 'abc'")
        self.assertTrue(nfa.matches("a#c"), "Dot: 'a.c' should match 'a#c'")
        self.assertFalse(nfa.matches("ac"), "Dot: 'a.c' should not match 'ac'")
    
    def test_grouping(self):
        nfa = build_nfa("(a|b)c")
        self.assertTrue(nfa.matches("ac"), "Grouping: '(a|b)c' should match 'ac'")
        self.assertTrue(nfa.matches("bc"), "Grouping: '(a|b)c' should match 'bc'")
        self.assertFalse(nfa.matches("cc"), "Grouping: '(a|b)c' should not match 'cc'")
    
    def test_complex_pattern_1(self):
        nfa = build_nfa("a(b|c)*d")
        self.assertTrue(nfa.matches("ad"), "Complex: 'a(b|c)*d' should match 'ad'")
        self.assertTrue(nfa.matches("abcd"), "Complex: 'a(b|c)*d' should match 'abcd'")
        self.assertTrue(nfa.matches("abcbcd"), "Complex: 'a(b|c)*d' should match 'abcbcd'")
        self.assertFalse(nfa.matches("aed"), "Complex: 'a(b|c)*d' should not match 'aed'")
    
    def test_complex_pattern_2(self):
        nfa = build_nfa("[0-9]+")
        self.assertTrue(nfa.matches("123"), "Complex: '[0-9]+' should match '123'")
        self.assertFalse(nfa.matches("abc"), "Complex: '[0-9]+' should not match 'abc'")
    
    def test_epsilon_closure(self):
        nfa = build_nfa("a*")
        start_closure = nfa.epsilon_closure({nfa.start})
        self.assertGreater(len(start_closure), 0, "Epsilon closure: start state should have epsilon transitions")
    
    def test_move_function(self):
        nfa = build_nfa("ab")
        start_closure = nfa.epsilon_closure({nfa.start})
        next_states = nfa.move(start_closure, 'a')
        self.assertGreater(len(next_states), 0, "Move: should transition on 'a'")

if __name__ == '__main__':
    unittest.main()
