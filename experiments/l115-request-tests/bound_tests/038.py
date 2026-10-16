import unittest

class TestRegexEngine(unittest.TestCase):
    def test_a_b_c_star_d_matches_ad(self):
        engine = RegexEngine()
        engine.compile("a(b|c)*d")
        self.assertTrue(engine.match("ad"), "Pattern should match 'ad'")

    def test_a_b_c_star_d_matches_abcd(self):
        engine = RegexEngine()
        engine.compile("a(b|c)*d")
        self.assertTrue(engine.match("abcd"), "Pattern should match 'abcd'")

    def test_a_b_c_star_d_matches_abcbcd(self):
        engine = RegexEngine()
        engine.compile("a(b|c)*d")
        self.assertTrue(engine.match("abcbcd"), "Pattern should match 'abcbcd'")

    def test_a_b_c_star_d_does_not_match_aed(self):
        engine = RegexEngine()
        engine.compile("a(b|c)*d")
        self.assertFalse(engine.match("aed"), "Pattern should not match 'aed'")

    def test_0_9_plus_matches_123(self):
        engine = RegexEngine()
        engine.compile("[0-9]+")
        self.assertTrue(engine.match("123"), "Pattern should match '123'")

    def test_0_9_plus_does_not_match_abc(self):
        engine = RegexEngine()
        engine.compile("[0-9]+")
        self.assertFalse(engine.match("abc"), "Pattern should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
