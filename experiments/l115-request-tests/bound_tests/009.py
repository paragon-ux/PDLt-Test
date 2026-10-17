import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_matches_pattern_with_grouping(self):
        # Test pattern: a(b|c)*d
        self.assertTrue(matches("a(b|c)*d", "ad"), "Should match 'ad'")
        self.assertTrue(matches("a(b|c)*d", "abcd"), "Should match 'abcd'")
        self.assertTrue(matches("a(b|c)*d", "abcbcd"), "Should match 'abcbcd'")
        self.assertFalse(matches("a(b|c)*d", "aed"), "Should not match 'aed'")
    
    def test_matches_character_class(self):
        # Test pattern: [0-9]+
        self.assertTrue(matches("[0-9]+", "123"), "Should match '123'")
        self.assertFalse(matches("[0-9]+", "abc"), "Should not match 'abc'")

if __name__ == '__main__':
    unittest.main()
