import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_example1_matches_ad(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("ad"), "Pattern 'a(b|c)*d' should match 'ad'")
    
    def test_example1_matches_abcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("abcd"), "Pattern 'a(b|c)*d' should match 'abcd'")
    
    def test_example1_matches_abcbcd(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertTrue(nfa.matches("abcbcd"), "Pattern 'a(b|c)*d' should match 'abcbcd'")
    
    def test_example1_not_match_aed(self):
        nfa = compile_regex("a(b|c)*d")
        self.assertFalse(nfa.matches("aed"), "Pattern 'a(b|c)*d' should not match 'aed'")
    
    def test_example2_matches_123(self):
        nfa = compile_regex("[0-9]+")
        self.assertTrue(nfa.matches("123"), "Pattern '[0-9]+' should match '123'")
    
    def test_example2_not_match_abc(self):
        nfa = compile_regex("[0-9]+")
        self.assertFalse(nfa.matches("abc"), "Pattern '[0-9]+' should not match 'abc'")
    
    def test_basic_concatenation(self):
        nfa = compile_regex("ab")
        self.assertTrue(nfa.matches("ab"), "Pattern 'ab' should match 'ab'")
        self.assertFalse(nfa.matches("a"), "Pattern 'ab' should not match 'a'")
        self.assertFalse(nfa.matches("b"), "Pattern 'ab' should not match 'b'")
    
    def test_kleene_star(self):
        nfa = compile_regex("a*")
        self.assertTrue(nfa.matches(""), "Pattern 'a*' should match empty string")
        self.assertTrue(nfa.matches("a"), "Pattern 'a*' should match 'a'")
        self.assertTrue(nfa.matches("aaa"), "Pattern 'a*' should match 'aaa'")
    
    def test_plus_operator(self):
        nfa = compile_regex("a+")
        self.assertFalse(nfa.matches(""), "Pattern 'a+' should not match empty string")
        self.assertTrue(nfa.matches("a"), "Pattern 'a+' should match 'a'")
        self.assertTrue(nfa.matches("aa"), "Pattern 'a+' should match 'aa'")
    
    def test_optional_operator(self):
        nfa = compile_regex("a?")
        self.assertTrue(nfa.matches(""), "Pattern 'a?' should match empty string")
        self.assertTrue(nfa.matches("a"), "Pattern 'a?' should match 'a'")
        self.assertFalse(nfa.matches("aa"), "Pattern 'a?' should not match 'aa'")
    
    def test_dot_matches_any_char(self):
        nfa = compile_regex("a.c")
        self.assertTrue(nfa.matches("abc"), "Pattern 'a.c' should match 'abc'")
        self.assertTrue(nfa.matches("axc"), "Pattern 'a.c' should match 'axc'")
        self.assertFalse(nfa.matches("ac"), "Pattern 'a.c' should not match 'ac'")
    
    def test_char_class_range(self):
        nfa = compile_regex("[a-z]")
        self.assertTrue(nfa.matches("m"), "Pattern '[a-z]' should match 'm'")
        self.assertFalse(nfa.matches("M"), "Pattern '[a-z]' should not match 'M'")
        self.assertFalse(nfa.matches("0"), "Pattern '[a-z]' should not match '0'")
    
    def test_nested_grouping(self):
        nfa = compile_regex("(a(b|c)*d)+")
        self.assertTrue(nfa.matches("ad"), "Pattern should match 'ad'")
        self.assertTrue(nfa.matches("abcd"), "Pattern should match 'abcd'")
        self.assertTrue(nfa.matches("adabcd"), "Pattern should match 'adabcd'")

if __name__ == '__main__':
    unittest.main()
