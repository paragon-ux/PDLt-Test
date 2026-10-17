def test_a_b_c_star_d_matches_ad():
    parser = RegexParser("a(b|c)*d")
    ast = parser.parse()
    builder = ThompsonBuilder(parser)
    nfa = builder.build(ast)
    assert nfa.matches("ad") == True, "Pattern 'a(b|c)*d' should match 'ad'"

def test_a_b_c_star_d_matches_abcd():
    parser = RegexParser("a(b|c)*d")
    ast = parser.parse()
    builder = ThompsonBuilder(parser)
    nfa = builder.build(ast)
    assert nfa.matches("abcd") == True, "Pattern 'a(b|c)*d' should match 'abcd'"

def test_a_b_c_star_d_matches_abcbcd():
    parser = RegexParser("a(b|c)*d")
    ast = parser.parse()
    builder = ThompsonBuilder(parser)
    nfa = builder.build(ast)
    assert nfa.matches("abcbcd") == True, "Pattern 'a(b|c)*d' should match 'abcbcd'"

def test_a_b_c_star_d_does_not_match_aed():
    parser = RegexParser("a(b|c)*d")
    ast = parser.parse()
    builder = ThompsonBuilder(parser)
    nfa = builder.build(ast)
    assert nfa.matches("aed") == False, "Pattern 'a(b|c)*d' should not match 'aed'"

def test_0_9_plus_matches_123():
    parser = RegexParser("[0-9]+")
    ast = parser.parse()
    builder = ThompsonBuilder(parser)
    nfa = builder.build(ast)
    assert nfa.matches("123") == True, "Pattern '[0-9]+' should match '123'"

def test_0_9_plus_does_not_match_abc():
    parser = RegexParser("[0-9]+")
    ast = parser.parse()
    builder = ThompsonBuilder(parser)
    nfa = builder.build(ast)
    assert nfa.matches("abc") == False, "Pattern '[0-9]+' should not match 'abc'"
