def test_pattern_a_b_c_star_d_matches_ad():
    assert Regex("a(b|c)*d").match("ad") is True, "Pattern should match 'ad'"

def test_pattern_a_b_c_star_d_matches_abcd():
    assert Regex("a(b|c)*d").match("abcd") is True, "Pattern should match 'abcd'"

def test_pattern_a_b_c_star_d_matches_abcbcd():
    assert Regex("a(b|c)*d").match("abcbcd") is True, "Pattern should match 'abcbcd'"

def test_pattern_a_b_c_star_d_does_not_match_aed():
    assert Regex("a(b|c)*d").match("aed") is False, "Pattern should not match 'aed'"

def test_pattern_0_9_plus_matches_123():
    assert Regex("[0-9]+").match("123") is True, "Pattern should match '123'"

def test_pattern_0_9_plus_does_not_match_abc():
    assert Regex("[0-9]+").match("abc") is False, "Pattern should not match 'abc'"
