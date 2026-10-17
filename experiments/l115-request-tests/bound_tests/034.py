import unittest

class TestThompsonConstruction(unittest.TestCase):
    def test_regex_a_b_c_star_d_matches_ad(self):
        regex = Regex("a(b|c)*d")
        self.assertTrue(regex.matches("ad"), "Should match 'ad'")

    def test_regex_a_b_c_star_d_matches_abcd(self):
        regex = Regex("a(b|c)*d")
        self.assertTrue(regex.matches("abcd"), "Should match 'abcd'")

    def test_regex_a_b_c_star_d_matches_abcbcd(self):
        regex = Regex("a(b|c)*d")
        self.assertTrue(regex.matches("abcbcd"), "Should match 'abcbcd'")

    def test_regex_a_b_c_star_d_does_not_match_aed(self):
        regex = Regex("a(b|c)*d")
        self.assertFalse(regex.matches("aed"), "Should not match 'aed'")

    def test_regex_0_9_plus_matches_123(self):
        regex = Regex("[0-9]+")
        self.assertTrue(regex.matches("123"), "Should match '123'")

    def test_regex_0_9_plus_does_not_match_abc(self):
        regex = Regex("[0-9]+")
        self.assertFalse(regex.matches("abc"), "Should not match 'abc'")

if __name__ == "__main__":
    unittest.main()
