import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_concatenation(self):
        r = Regex("ab")
        self.assertTrue(r.match("ab"))
        self.assertFalse(r.match("a"))
        self.assertFalse(r.match("b"))
        self.assertFalse(r.match("abc"))
    
    def test_alternation(self):
        r = Regex("a|b")
        self.assertTrue(r.match("a"))
        self.assertTrue(r.match("b"))
        self.assertFalse(r.match("c"))
        self.assertFalse(r.match("ab"))
    
    def test_kleene_star(self):
        r = Regex("a*")
        self.assertTrue(r.match(""))
        self.assertTrue(r.match("a"))
        self.assertTrue(r.match("aa"))
        self.assertTrue(r.match("aaa"))
        self.assertFalse(r.match("b"))
    
    def test_plus(self):
        r = Regex("a+")
        self.assertFalse(r.match(""))
        self.assertTrue(r.match("a"))
        self.assertTrue(r.match("aa"))
        self.assertFalse(r.match("b"))
    
    def test_optional(self):
        r = Regex("a?")
        self.assertTrue(r.match(""))
        self.assertTrue(r.match("a"))
        self.assertFalse(r.match("aa"))
        self.assertFalse(r.match("b"))
    
    def test_character_class(self):
        r = Regex("[a-z]")
        self.assertTrue(r.match("a"))
        self.assertTrue(r.match("z"))
        self.assertFalse(r.match("A"))
        self.assertFalse(r.match("0"))
    
    def test_negated_character_class(self):
        r = Regex("[^a-z]")
        self.assertFalse(r.match("a"))
        self.assertFalse(r.match("z"))
        self.assertTrue(r.match("A"))
        self.assertTrue(r.match("0"))
    
    def test_dot(self):
        r = Regex("a.b")
        self.assertTrue(r.match("acb"))
        self.assertTrue(r.match("azb"))
        self.assertFalse(r.match("ab"))
        self.assertFalse(r.match("a"))
    
    def test_grouping(self):
        r = Regex("(a|b)c")
        self.assertTrue(r.match("ac"))
        self.assertTrue(r.match("bc"))
        self.assertFalse(r.match("cc"))
        self.assertFalse(r.match("abc"))
    
    def test_complex_pattern(self):
        r = Regex("a(b|c)*d")
        self.assertTrue(r.match("ad"))
        self.assertTrue(r.match("abcd"))
        self.assertTrue(r.match("abcbcd"))
        self.assertFalse(r.match("aed"))
    
    def test_digit_class_plus(self):
        r = Regex("[0-9]+")
        self.assertTrue(r.match("123"))
        self.assertFalse(r.match("abc"))
        self.assertFalse(r.match(""))
    
    def test_nested_operators(self):
        r = Regex("(ab)*c")
        self.assertTrue(r.match("c"))
        self.assertTrue(r.match("abc"))
        self.assertTrue(r.match("abababc"))
        self.assertFalse(r.match("ac"))
        self.assertFalse(r.match("ab"))
    
    def test_empty_string(self):
        r = Regex("")
        self.assertTrue(r.match(""))
        self.assertFalse(r.match("a"))
    
    def test_single_literal(self):
        r = Regex("a")
        self.assertTrue(r.match("a"))
        self.assertFalse(r.match(""))
        self.assertFalse(r.match("b"))
    
    def test_multiple_alternatives(self):
        r = Regex("a|b|c")
        self.assertTrue(r.match("a"))
        self.assertTrue(r.match("b"))
        self.assertTrue(r.match("c"))
        self.assertFalse(r.match("d"))
    
    def test_mixed_operators(self):
        r = Regex("a(b|c)*d?")
        self.assertTrue(r.match("ad"))
        self.assertTrue(r.match("abd"))
        self.assertTrue(r.match("acd"))
        self.assertTrue(r.match("abcbcd"))
        self.assertTrue(r.match("a"))
        self.assertFalse(r.match("ae"))
        self.assertFalse(r.match("ab"))
