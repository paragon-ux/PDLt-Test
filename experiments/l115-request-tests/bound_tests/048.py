def test_a_b_c_star_d_matches_ad():
    assert match("a(b|c)*d", "ad"), "Pattern 'a(b|c)*d' should match 'ad'"

def test_a_b_c_star_d_matches_abcd():
    assert match("a(b|c)*d", "abcd"), "Pattern 'a(b|c)*d' should match 'abcd'"

def test_a_b_c_star_d_matches_abcbcd():
    assert match("a(b|c)*d", "abcbcd"), "Pattern 'a(b|c)*d' should match 'abcbcd'"

def test_a_b_c_star_d_does_not_match_aed():
    assert not match("a(b|c)*d", "aed"), "Pattern 'a(b|c)*d' should not match 'aed'"

def test_digit_plus_matches_123():
    assert match("[0-9]+", "123"), "Pattern '[0-9]+' should match '123'"

def test_digit_plus_does_not_match_abc():
    assert not match("[0-9]+", "abc"), "Pattern '[0-9]+' should not match 'abc'"

if __name__ == "__main__":
    test_a_b_c_star_d_matches_ad()
    test_a_b_c_star_d_matches_abcd()
    test_a_b_c_star_d_matches_abcbcd()
    test_a_b_c_star_d_does_not_match_aed()
    test_digit_plus_matches_123()
    test_digit_plus_does_not_match_abc()
    print("All tests passed")