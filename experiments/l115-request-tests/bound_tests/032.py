import unittest

class TestThompsonConstruction(unittest.TestCase):
    def test_ad_matches(self):
        engine = RegexEngine()
        self.assertTrue(engine.match("a(b|c)*d", "ad"), "Pattern 'a(b|c)*d' should match 'ad'")

    def test_abcd_matches(self):
        engine = RegexEngine()
        self.assertTrue(engine.match("a(b|c)*d", "abcd"), "Pattern 'a(b|c)*d' should match 'abcd'")

    def test_abcbcd_matches(self):
        engine = RegexEngine()
        self.assertTrue(engine.match("a(b|c)*d", "abcbcd"), "Pattern 'a(b|c)*d' should match 'abcbcd'")

    def test_aed_does_not_match(self):
        engine = RegexEngine()
        self.assertFalse(engine.match("a(b|c)*d", "aed"), "Pattern 'a(b|c)*d' should not match 'aed'")

    def test_123_matches(self):
        engine = RegexEngine()
        self.assertTrue(engine.match("[0-9]+", "123"), "Pattern '[0-9]+' should match '123'")

    def test_abc_does_not_match(self):
        engine = RegexEngine()
        self.assertFalse(engine.match("[0-9]+", "abc"), "Pattern '[0-9]+' should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
