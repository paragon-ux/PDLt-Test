def test_a_b_c_star_d_matches_ad():
    engine = RegexEngine()
    engine.compile("a(b|c)*d")
    assert engine.match("ad") is True, "Pattern 'a(b|c)*d' should match 'ad'"

def test_a_b_c_star_d_matches_abcd():
    engine = RegexEngine()
    engine.compile("a(b|c)*d")
    assert engine.match("abcd") is True, "Pattern 'a(b|c)*d' should match 'abcd'"

def test_a_b_c_star_d_matches_abcbcd():
    engine = RegexEngine()
    engine.compile("a(b|c)*d")
    assert engine.match("abcbcd") is True, "Pattern 'a(b|c)*d' should match 'abcbcd'"

def test_a_b_c_star_d_does_not_match_aed():
    engine = RegexEngine()
    engine.compile("a(b|c)*d")
    assert engine.match("aed") is False, "Pattern 'a(b|c)*d' should not match 'aed'"

def test_0_9_plus_matches_123():
    engine = RegexEngine()
    engine.compile("[0-9]+")
    assert engine.match("123") is True, "Pattern '[0-9]+' should match '123'"

def test_0_9_plus_does_not_match_abc():
    engine = RegexEngine()
    engine.compile("[0-9]+")
    assert engine.match("abc") is False, "Pattern '[0-9]+' should not match 'abc'"
