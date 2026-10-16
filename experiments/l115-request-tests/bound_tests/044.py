def test_pattern_a_b_c_star_d_matches_ad():
    nfa = ThompsonNFA("a(b|c)*d")
    assert nfa.matches("ad"), "Expected match for 'ad'"

def test_pattern_a_b_c_star_d_matches_abcd():
    nfa = ThompsonNFA("a(b|c)*d")
    assert nfa.matches("abcd"), "Expected match for 'abcd'"

def test_pattern_a_b_c_star_d_matches_abcbcd():
    nfa = ThompsonNFA("a(b|c)*d")
    assert nfa.matches("abcbcd"), "Expected match for 'abcbcd'"

def test_pattern_a_b_c_star_d_does_not_match_aed():
    nfa = ThompsonNFA("a(b|c)*d")
    assert not nfa.matches("aed"), "Expected no match for 'aed'"

def test_pattern_0_9_plus_matches_123():
    nfa = ThompsonNFA("[0-9]+")
    assert nfa.matches("123"), "Expected match for '123'"

def test_pattern_0_9_plus_does_not_match_abc():
    nfa = ThompsonNFA("[0-9]+")
    assert not nfa.matches("abc"), "Expected no match for 'abc'"