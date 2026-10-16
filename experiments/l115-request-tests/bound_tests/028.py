def test_regex_a_b_c_d_matches_ad():
    r = Regex("a(b|c)*d")
    assert r.matches("ad"), "Expected 'ad' to match 'a(b|c)*d'"

def test_regex_a_b_c_d_matches_abcd():
    r = Regex("a(b|c)*d")
    assert r.matches("abcd"), "Expected 'abcd' to match 'a(b|c)*d'"

def test_regex_a_b_c_d_matches_abcbcd():
    r = Regex("a(b|c)*d")
    assert r.matches("abcbcd"), "Expected 'abcbcd' to match 'a(b|c)*d'"

def test_regex_a_b_c_d_does_not_match_aed():
    r = Regex("a(b|c)*d")
    assert not r.matches("aed"), "Expected 'aed' not to match 'a(b|c)*d'"

def test_regex_char_class_matches_123():
    r = Regex("[0-9]+")
    assert r.matches("123"), "Expected '123' to match '[0-9]+'"

def test_regex_char_class_does_not_match_abc():
    r = Regex("[0-9]+")
    assert not r.matches("abc"), "Expected 'abc' not to match '[0-9]+'"
