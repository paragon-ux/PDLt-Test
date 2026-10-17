import unittest

class TestThompsonConstruction(unittest.TestCase):
    
    def test_matches_a_b_c_star_d_ad(self):
        self.assertTrue(matches("a(b|c)*d", "ad"))
        
    def test_matches_a_b_c_star_d_abcd(self):
        self.assertTrue(matches("a(b|c)*d", "abcd"))
        
    def test_matches_a_b_c_star_d_abcbcd(self):
        self.assertTrue(matches("a(b|c)*d", "abcbcd"))
        
    def test_matches_a_b_c_star_d_aed_not_match(self):
        self.assertFalse(matches("a(b|c)*d", "aed"))
        
    def test_matches_0_9_plus_123(self):
        self.assertTrue(matches("[0-9]+", "123"))
        
    def test_matches_0_9_plus_abc_not_match(self):
        self.assertFalse(matches("[0-9]+", "abc"))

class TestTokenization(unittest.TestCase):
    
    def test_tokenize_basic_operators(self):
        tokens = tokenize("a|b*")
        self.assertEqual(tokens, ['a', '|', 'b', '*'])
        
    def test_tokenize_parentheses(self):
        tokens = tokenize("(ab)*")
        self.assertEqual(tokens, ['(', 'a', 'b', ')', '*'])
        
    def test_tokenize_character_class(self):
        tokens = tokenize("[a-z]+")
        self.assertEqual(tokens, ['[a-z]', '+'])

class TestInsertConcat(unittest.TestCase):
    
    def test_insert_concat_implicit(self):
        tokens = tokenize("ab")
        result = insert_concat(tokens)
        self.assertEqual(result, ['a', '.', 'b'])
        
    def test_insert_concat_with_operators(self):
        tokens = tokenize("a|b")
        result = insert_concat(tokens)
        self.assertEqual(result, ['a', '|', 'b'])

class TestToPostfix(unittest.TestCase):
    
    def test_to_postfix_simple_concat(self):
        tokens = insert_concat(tokenize("ab"))
        postfix = to_postfix(tokens)
        self.assertEqual(postfix, ['a', 'b', '.'])
        
    def test_to_postfix_alternation(self):
        tokens = insert_concat(tokenize("a|b"))
        postfix = to_postfix(tokens)
        self.assertEqual(postfix, ['a', 'b', '|'])

class TestStateClass(unittest.TestCase):
    
    def test_state_initialization(self):
        state = State(accept=True)
        self.assertTrue(state.accept)
        self.assertEqual(state.transitions, {})
        
    def test_add_transition(self):
        state1 = State(accept=False)
        state2 = State(accept=True)
        state1.add_transition('a', state2)
        self.assertIn('a', state1.transitions)
        self.assertEqual(state1.transitions['a'], [state2])

class TestEpsilonClosure(unittest.TestCase):
    
    def test_epsilon_closure_single_state(self):
        state = State(accept=False)
        closure = epsilon_closure([state])
        self.assertIn(state, closure)
        
    def test_epsilon_closure_with_epsilon_transitions(self):
        state1 = State(accept=False)
        state2 = State(accept=True)
        state1.add_transition(None, state2)  # None represents epsilon
        closure = epsilon_closure([state1])
        self.assertIn(state1, closure)
        self.assertIn(state2, closure)

class TestMoveFunction(unittest.TestCase):
    
    def test_move_basic(self):
        state1 = State(accept=False)
        state2 = State(accept=True)
        state1.add_transition('a', state2)
        result = move([state1], 'a')
        self.assertIn(state2, result)
        
    def test_move_no_transition(self):
        state1 = State(accept=False)
        result = move([state1], 'a')
        self.assertEqual(result, set())

class TestFragmentClass(unittest.TestCase):
    
    def test_fragment_initialization(self):
        start = State(accept=False)
        accept = State(accept=True)
        fragment = Fragment(start, accept)
        self.assertEqual(fragment.start, start)
        self.assertEqual(fragment.accept, accept)

class TestThompsonConstructionFunction(unittest.TestCase):
    
    def test_thompson_simple_char(self):
        postfix = ['a']
        fragment = thompson(postfix)
        self.assertIsInstance(fragment, Fragment)
        self.assertFalse(fragment.start.accept)
        self.assertTrue(fragment.accept.accept)

if __name__ == '__main__':
    unittest.main()
