import re
from typing import List, Tuple

def check_password_strength(password: str) -> Tuple[str, List[str]]:
    """Evaluate password strength and provide improvement suggestions.

    Returns a tuple of (strength_level, suggestions). Strength levels are
    'weak', 'medium', or 'strong' as defined by the specification.
    """
    suggestions = []
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_letter = any(c.isalpha() for c in password)
    has_special = bool(re.search(r'[!@#$%^&*]', password))

    # Weak criteria
    if length < 8:
        strength = 'weak'
        suggestions.append('Increase length to at least 8 characters.')
    elif password.isalpha():
        strength = 'weak'
        suggestions.append('Add digits or special characters to the password.')
    else:
        # Medium criteria
        if 8 <= length <= 12 and has_letter and has_digit:
            strength = 'medium'
            if not has_upper:
                suggestions.append('Add uppercase letters to strengthen the password.')
            if not has_lower:
                suggestions.append('Add lowercase letters to strengthen the password.')
            if not has_special:
                suggestions.append('Add a special character (!@#$%^&*) to strengthen the password.')
        else:
            # Strong criteria
            if length > 12 and has_upper and has_lower and has_digit and has_special:
                strength = 'strong'
                # No suggestions needed for a strong password
            else:
                # Does not meet strong criteria, downgrade to medium with suggestions
                strength = 'medium'
                if length <= 12:
                    suggestions.append('Increase length to more than 12 characters.')
                if not has_upper:
                    suggestions.append('Add uppercase letters.')
                if not has_lower:
                    suggestions.append('Add lowercase letters.')
                if not has_digit:
                    suggestions.append('Add digits.')
                if not has_special:
                    suggestions.append('Add a special character (!@#$%^&*).')
    return strength, suggestions

# Test suite
import unittest

class TestPasswordStrengthChecker(unittest.TestCase):
    def test_weak_short(self):
        strength, suggestions = check_password_strength('abc')
        self.assertEqual(strength, 'weak')
        self.assertIn('Increase length to at least 8 characters.', suggestions)

    def test_weak_letters_only(self):
        strength, suggestions = check_password_strength('abcdefgh')
        self.assertEqual(strength, 'weak')
        self.assertIn('Add digits or special characters to the password.', suggestions)

    def test_medium_boundary(self):
        strength, suggestions = check_password_strength('Abcdef12')
        self.assertEqual(strength, 'medium')
        self.assertIn('Add a special character (!@#$%^&*) to strengthen the password.', suggestions)

    def test_medium_missing_digit(self):
        strength, suggestions = check_password_strength('Abcdefgh')
        self.assertEqual(strength, 'medium')
        self.assertIn('Add digits or special characters to the password.', suggestions)

    def test_strong(self):
        strength, suggestions = check_password_strength('Abcdef12!@#')
        self.assertEqual(strength, 'strong')
        self.assertEqual(suggestions, [])

    def test_strong_long(self):
        strength, suggestions = check_password_strength('AveryStrongPassword123!')
        self.assertEqual(strength, 'strong')
        self.assertEqual(suggestions, [])

if __name__ == '__main__':
    unittest.main()
