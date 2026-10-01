def check_password_strength(password: str):
    """Return a tuple (strength, suggestions).
    strength: 'weak', 'medium', or 'strong'
    suggestions: list of strings describing unmet criteria for the determined level.
    """
    import re
    suggestions = []
    length = len(password)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_letter = any(c.isalpha() for c in password)
    special_chars = set('!@#$%^&*')
    has_special = any(c in special_chars for c in password)
    only_letters = all(c.isalpha() for c in password) and password != ''
    # Determine strength
    if length < 8 or only_letters:
        strength = "weak"
        if length < 8:
            suggestions.append("Increase length to at least 8 characters.")
        if only_letters:
            suggestions.append("Include digits or special characters.")
    elif 8 <= length <= 12 and has_letter and has_digit:
        strength = "medium"
        if not has_letter:
            suggestions.append("Add at least one letter.")
        if not has_digit:
            suggestions.append("Add at least one digit.")
        if length < 8:
            suggestions.append("Increase length to at least 8 characters.")
        if length > 12:
            suggestions.append("Increase length beyond 12 for stronger strength.")
    elif length > 12 and has_upper and has_lower and has_digit and has_special:
        strength = "strong"
        # Strong meets all criteria, no suggestions
    else:
        # Falls into medium or weak depending on which criteria are missing
        if length > 12:
            strength = "medium"
            suggestions.append("Include uppercase letters, lowercase letters, digits, and at least one special character (!@#$%^&*).")
        else:
            strength = "weak"
            if length < 8:
                suggestions.append("Increase length to at least 8 characters.")
            if not has_letter:
                suggestions.append("Add at least one letter.")
            if not has_digit:
                suggestions.append("Add at least one digit.")
    return strength, suggestions

# Simple test suite
if __name__ == "__main__":
    test_cases = {
        "abc": ("weak", ["Increase length to at least 8 characters.", "Include digits or special characters."]),
        "abcdefgh": ("weak", ["Include digits or special characters."]),
        "abc12345": ("medium", []),
        "ABCdef12345!": ("strong", []),
        "short1": ("weak", ["Increase length to at least 8 characters."]),
    }
    for pwd, expected in test_cases.items():
        result = check_password_strength(pwd)
        assert result[0] == expected[0], f"{pwd}: expected strength {expected[0]}, got {result[0]}"
        # suggestions may differ in order or extra messages; we check inclusion
        for exp_msg in expected[1]:
            assert exp_msg in result[1], f"{pwd}: missing suggestion '{exp_msg}'"
    print("All tests passed.")
