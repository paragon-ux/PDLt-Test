def test_regex_match_a_b_or_c_star_d():
    # Test cases for regex "a(b|c)*d"
    assert match("a(b|c)*d", "ad") is True, "Failed: 'ad' should match 'a(b|c)*d'"
    assert match("a(b|c)*d", "abcd") is True, "Failed: 'abcd' should match 'a(b|c)*d'"
    assert match("a(b|c)*d", "abcbcd") is True, "Failed: 'abcbcd' should match 'a(b|c)*d'"
    assert match("a(b|c)*d", "aed") is False, "Failed: 'aed' should not match 'a(b|c)*d'"

def test_regex_match_0_9_plus():
    # Test cases for regex "[0-9]+"
    assert match("[0-9]+", "123") is True, "Failed: '123' should match '[0-9]+'"
    assert match("[0-9]+", "abc") is False, "Failed: 'abc' should not match '[0-9]+'"
