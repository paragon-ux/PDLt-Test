def test_a_b_c_star_d_matches_ad():
    assert regex_match("a(b|c)*d", "ad"), "Expected 'ad' to match 'a(b|c)*d'"

def test_a_b_c_star_d_matches_abcd():
    assert regex_match("a(b|c)*d", "abcd"), "Expected 'abcd' to match 'a(b|c)*d'"

def test_a_b_c_star_d_matches_abcbcd():
    assert regex_match("a(b|c)*d", "abcbcd"), "Expected 'abcbcd' to match 'a(b|c)*d'"

def test_a_b_c_star_d_does_not_match_aed():
    assert not regex_match("a(b|c)*d", "aed"), "Expected 'aed' not to match 'a(b|c)*d'"

def test_char_class_0_9_plus_matches_123():
    assert regex_match("[0-9]+", "123"), "Expected '123' to match '[0-9]+'"

def test_char_class_0_9_plus_does_not_match_abc():
    assert not regex_match("[0-9]+", "abc"), "Expected 'abc' not to match '[0-9]+'"
