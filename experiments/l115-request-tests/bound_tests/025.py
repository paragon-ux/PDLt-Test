def test_match_a_b_c_star_d_ad():
    assert match("a(b|c)*d", "ad") == True, "Pattern 'a(b|c)*d' should match 'ad'"

def test_match_a_b_c_star_d_abcd():
    assert match("a(b|c)*d", "abcd") == True, "Pattern 'a(b|c)*d' should match 'abcd'"

def test_match_a_b_c_star_d_abcbcd():
    assert match("a(b|c)*d", "abcbcd") == True, "Pattern 'a(b|c)*d' should match 'abcbcd'"

def test_match_a_b_c_star_d_aed():
    assert match("a(b|c)*d", "aed") == False, "Pattern 'a(b|c)*d' should not match 'aed'"

def test_match_0_9_plus_123():
    assert match("[0-9]+", "123") == True, "Pattern '[0-9]+' should match '123'"

def test_match_0_9_plus_abc():
    assert match("[0-9]+", "abc") == False, "Pattern '[0-9]+' should not match 'abc'"
