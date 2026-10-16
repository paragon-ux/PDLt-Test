import unittest

class TestThompsonConstruction(unittest.TestCase):
    def test_concat_basic(self):
        matcher = compile_regex("ab")
        self.assertTrue(matcher.matches("ab"), "Concatenation should match exact sequence")
        self.assertFalse(matcher.matches("ba"), "Concatenation should not match reversed sequence")
        self.assertFalse(matcher.matches("a"), "Concatenation should not match incomplete sequence")

    def test_alternation_simple(self):
        matcher = compile_regex("a|b")
        self.assertTrue(matcher.matches("a"), "Alternation should match first option")
        self.assertTrue(matcher.matches("b"), "Alternation should match second option")
        self.assertFalse(matcher.matches("c"), "Alternation should not match unrelated character")

    def test_kleene_star_zero_or_more(self):
        matcher = compile_regex("a*")
        self.assertTrue(matcher.matches(""), "Star should match empty string")
        self.assertTrue(matcher.matches("a"), "Star should match single occurrence")
        self.assertTrue(matcher.matches("aaa"), "Star should match multiple occurrences")

    def test_plus_one_or_more(self):
        matcher = compile_regex("a+")
        self.assertFalse(matcher.matches(""), "Plus should not match empty string")
        self.assertTrue(matcher.matches("a"), "Plus should match single occurrence")
        self.assertTrue(matcher.matches("aaaa"), "Plus should match multiple occurrences")

    def test_optional_zero_or_one(self):
        matcher = compile_regex("a?")
        self.assertTrue(matcher.matches(""), "Optional should match empty string")
        self.assertTrue(matcher.matches("a"), "Optional should match single occurrence")
        self.assertFalse(matcher.matches("aa"), "Optional should not match multiple occurrences")

    def test_dot_matches_any_character(self):
        matcher = compile_regex("a.c")
        self.assertTrue(matcher.matches("abc"), "Dot should match any single character")
        self.assertTrue(matcher.matches("a c"), "Dot should match space")
        self.assertTrue(matcher.matches("a1c"), "Dot should match digit")
        self.assertFalse(matcher.matches("ac"), "Dot should require exactly one character")

    def test_character_class_basic(self):
        matcher = compile_regex("[abc]")
        self.assertTrue(matcher.matches("a"), "Char class should match included character")
        self.assertTrue(matcher.matches("b"), "Char class should match included character")
        self.assertTrue(matcher.matches("c"), "Char class should match included character")
        self.assertFalse(matcher.matches("d"), "Char class should not match excluded character")

    def test_character_class_range(self):
        matcher = compile_regex("[0-9]")
        self.assertTrue(matcher.matches("5"), "Char class range should match digit in range")
        self.assertFalse(matcher.matches("a"), "Char class range should not match letter")

    def test_grouping_with_parentheses(self):
        matcher = compile_regex("(ab)+")
        self.assertTrue(matcher.matches("ab"), "Group with plus should match single occurrence")
        self.assertTrue(matcher.matches("abab"), "Group with plus should match multiple occurrences")
        self.assertFalse(matcher.matches("a"), "Group with plus should not match partial group")

    def test_complex_pattern_example1(self):
        matcher = compile_regex("a(b|c)*d")
        self.assertTrue(matcher.matches("ad"), "Pattern should match ad")
        self.assertTrue(matcher.matches("abcd"), "Pattern should match abcd")
        self.assertTrue(matcher.matches("abcbcd"), "Pattern should match abcbcd")
        self.assertFalse(matcher.matches("aed"), "Pattern should not match aed")

    def test_complex_pattern_example2(self):
        matcher = compile_regex("[0-9]+")
        self.assertTrue(matcher.matches("123"), "Pattern should match digits")
        self.assertFalse(matcher.matches("abc"), "Pattern should not match letters")

    def test_nested_operations(self):
        matcher = compile_regex("(a|b)*c")
        self.assertTrue(matcher.matches("c"), "Should match just c")
        self.assertTrue(matcher.matches("ac"), "Should match ac")
        self.assertTrue(matcher.matches("bc"), "Should match bc")
        self.assertTrue(matcher.matches("ababc"), "Should match complex sequence")
        self.assertFalse(matcher.matches("abcd"), "Should not match extra character")

    def test_empty_pattern(self):
        matcher = compile_regex("")
        self.assertTrue(matcher.matches(""), "Empty pattern should match empty string")
        self.assertFalse(matcher.matches("a"), "Empty pattern should not match non-empty string")

if __name__ == '__main__':
    unittest.main()
