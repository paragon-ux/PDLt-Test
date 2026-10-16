import unittest

class TestThompsonConstruction(unittest.TestCase):
    def test_example1_matches_ad(self):
        nfa = RegexNFA("a(b|c)*d")
        self.assertTrue(nfa.match("ad"), "Should match 'ad'")

    def test_example1_matches_abcd(self):
        nfa = RegexNFA("a(b|c)*d")
        self.assertTrue(nfa.match("abcd"), "Should match 'abcd'")

    def test_example1_matches_abcbcd(self):
        nfa = RegexNFA("a(b|c)*d")
        self.assertTrue(nfa.match("abcbcd"), "Should match 'abcbcd'")

    def test_example1_not_match_aed(self):
        nfa = RegexNFA("a(b|c)*d")
        self.assertFalse(nfa.match("aed"), "Should not match 'aed'")

    def test_example2_matches_123(self):
        nfa = RegexNFA("[0-9]+")
        self.assertTrue(nfa.match("123"), "Should match '123'")

    def test_example2_not_match_abc(self):
        nfa = RegexNFA("[0-9]+")
        self.assertFalse(nfa.match("abc"), "Should not match 'abc'")

    def test_epsilon_closure_exists(self):
        # Test that epsilon_closure function exists and is callable
        self.assertTrue(callable(epsilon_closure))

    def test_move_exists(self):
        # Test that move function exists and is callable
        self.assertTrue(callable(move))

    def test_matches_exists(self):
        # Test that matches function exists and is callable
        self.assertTrue(callable(matches))

    def test_fragment_class_exists(self):
        # Test that Fragment class exists and can be instantiated
        fragment = Fragment(None, None)
        self.assertIsNotNone(fragment)

    def test_parser_class_exists(self):
        # Test that Parser class exists and can be instantiated
        parser = Parser("a")
        self.assertIsNotNone(parser)

    def test_thompson_builder_class_exists(self):
        # Test that ThompsonBuilder class exists and can be instantiated
        builder = ThompsonBuilder()
        self.assertIsNotNone(builder)

    def test_regex_nfa_class_exists(self):
        # Test that RegexNFA class exists and can be instantiated
        nfa = RegexNFA("a")
        self.assertIsNotNone(nfa)
        self.assertTrue(hasattr(nfa, 'match'))

if __name__ == '__main__':
    unittest.main()
