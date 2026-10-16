def test_a_b_c_star_d_matches_ad():
    assert match("a(b|c)*d", "ad") == True, "Pattern 'a(b|c)*d' should match 'ad'"

def test_a_b_c_star_d_matches_abcd():
    assert match("a(b|c)*d", "abcd") == True, "Pattern 'a(b|c)*d' should match 'abcd'"

def test_a_b_c_star_d_matches_abcbcd():
    assert match("a(b|c)*d", "abcbcd") == True, "Pattern 'a(b|c)*d' should match 'abcbcd'"

def test_a_b_c_star_d_does_not_match_aed():
    assert match("a(b|c)*d", "aed") == False, "Pattern 'a(b|c)*d' should not match 'aed'"

def test_0_9_plus_matches_123():
    assert match("[0-9]+", "123") == True, "Pattern '[0-9]+' should match '123'"

def test_0_9_plus_does_not_match_abc():
    assert match("[0-9]+", "abc") == False, "Pattern '[0-9]+' should not match 'abc'"

def test_epsilon_closure_with_single_state():
    state = State()
    closure = epsilon_closure({state})
    assert state in closure, "Epsilon closure should include the initial state"

def test_move_with_matching_character():
    state1 = State()
    state2 = State()
    state1.add_transition('a', state2)
    result = move({state1}, 'a')
    assert state2 in result, "Move should transition on matching character"

def test_nfa_simulation_basic_match():
    nfa = compile_regex("a")
    assert simulate(nfa, "a") == True, "NFA simulation should match 'a'"

def test_nfa_simulation_no_match():
    nfa = compile_regex("a")
    assert simulate(nfa, "b") == False, "NFA simulation should not match 'b'"

def test_regex_parser_concatenation():
    nfa = compile_regex("ab")
    assert simulate(nfa, "ab") == True, "Concatenation pattern 'ab' should match 'ab'"
    assert simulate(nfa, "a") == False, "Concatenation pattern 'ab' should not match 'a'"

def test_regex_parser_alternation():
    nfa = compile_regex("a|b")
    assert simulate(nfa, "a") == True, "Alternation pattern 'a|b' should match 'a'"
    assert simulate(nfa, "b") == True, "Alternation pattern 'a|b' should match 'b'"
    assert simulate(nfa, "c") == False, "Alternation pattern 'a|b' should not match 'c'"

def test_kleene_star_zero_or_more():
    nfa = compile_regex("a*")
    assert simulate(nfa, "") == True, "Kleene star pattern 'a*' should match empty string"
    assert simulate(nfa, "a") == True, "Kleene star pattern 'a*' should match 'a'"
    assert simulate(nfa, "aaa") == True, "Kleene star pattern 'a*' should match 'aaa'"

def test_plus_one_or_more():
    nfa = compile_regex("a+")
    assert simulate(nfa, "") == False, "Plus pattern 'a+' should not match empty string"
    assert simulate(nfa, "a") == True, "Plus pattern 'a+' should match 'a'"
    assert simulate(nfa, "aaa") == True, "Plus pattern 'a+' should match 'aaa'"

def test_optional_zero_or_one():
    nfa = compile_regex("a?")
    assert simulate(nfa, "") == True, "Optional pattern 'a?' should match empty string"
    assert simulate(nfa, "a") == True, "Optional pattern 'a?' should match 'a'"
    assert simulate(nfa, "aa") == False, "Optional pattern 'a?' should not match 'aa'"

def test_character_class():
    nfa = compile_regex("[a-z]")
    assert simulate(nfa, "a") == True, "Character class '[a-z]' should match 'a'"
    assert simulate(nfa, "z") == True, "Character class '[a-z]' should match 'z'"
    assert simulate(nfa, "A") == False, "Character class '[a-z]' should not match 'A'"

def test_dot_matches_any_character():
    nfa = compile_regex(".")
    assert simulate(nfa, "a") == True, "Dot pattern should match any character"
    assert simulate(nfa, "1") == True, "Dot pattern should match any character"
    assert simulate(nfa, " ") == True, "Dot pattern should match any character"

def test_grouping_with_parentheses():
    nfa = compile_regex("(a|b)c")
    assert simulate(nfa, "ac") == True, "Grouped pattern '(a|b)c' should match 'ac'"
    assert simulate(nfa, "bc") == True, "Grouped pattern '(a|b)c' should match 'bc'"
    assert simulate(nfa, "cc") == False, "Grouped pattern '(a|b)c' should not match 'cc'"
