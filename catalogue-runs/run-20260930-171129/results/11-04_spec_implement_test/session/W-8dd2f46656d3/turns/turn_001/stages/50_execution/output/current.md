# password_checker.py
"""Password strength checker implementation.

Provides a function `check_password` that returns a tuple `(strength, suggestions)`
according to the confirmed specification.
"""
import re
from typing import List, Tuple

SPECIAL_CHARS = set('!@#$%^&*')

def check_password(pw: str) -> Tuple[str, List[str]]:
    """Evaluate password strength and generate improvement suggestions.

    Returns:
        strength: 'weak', 'medium', or 'strong'
        suggestions: list of human‑readable suggestions
    """
    suggestions: List[str] = []
    length = len(pw)
    has_lower = any(c.islower() for c in pw)
    has_upper = any(c.isupper() for c in pw)
    has_digit = any(c.isdigit() for c in pw)
    has_letter = any(c.isalpha() for c in pw)
    has_special = any(c in SPECIAL_CHARS for c in pw)

    # Determine strength
    if length < 8 or (has_letter and not (has_upper or has_lower or has_digit or has_special)):
        strength = 'weak'
    elif 8 <= length <= 12 and has_letter and has_digit:
        strength = 'medium'
    elif (length > 12 and has_upper and has_lower and has_digit and has_special):
        strength = 'strong'
    else:
        # Falls outside defined categories, treat as weak
        strength = 'weak'

    # Generate suggestions
    if length < 8:
        suggestions.append('Increase length to at least 8 characters')
    if not has_letter:
        suggestions.append('Add at least one letter')
    if not has_digit:
        suggestions.append('Add at least one digit')
    if length > 12:
        if not has_upper:
            suggestions.append('Add uppercase letters')
        if not has_lower:
            suggestions.append('Add lowercase letters')
        if not has_digit:
            suggestions.append('Add digits')
        if not has_special:
            suggestions.append('Add a special character from !@#$%^&*')
    return strength, suggestions

# Example usage (can be removed in production)
if __name__ == "__main__":
    test_pw = "Example1!"
    lvl, sug = check_password(test_pw)
    print(f"Strength: {lvl}")
    print("Suggestions:")
    for s in sug:
        print(f"- {s}")

---
{"files":[{"filename":"password_checker.py","satisfies":["R1","R2","R3","R4","R5"],"evidence":{"path":"execution://body","section":"check_password implementation","observed":"def check_password(pw: str) -> Tuple[str, List[str]]:"}}],"reconciliation":[{"requirement":"R1","status":"satisfied","evidence":{"path":"execution://body","section":"READ input","observed":"def check_password(pw: str)"}},{"requirement":"R2","status":"satisfied","evidence":{"path":"execution://body","section":"SET strength to weak","observed":"strength = 'weak'"}},{"requirement":"R3","status":"satisfied","evidence":{"path":"execution://body","section":"SET strength to medium","observed":"strength = 'medium'"}},{"requirement":"R4","status":"satisfied","evidence":{"path":"execution://body","section":"SET strength to strong","observed":"strength = 'strong'"}},{"requirement":"R5","status":"satisfied","evidence":{"path":"execution://body","section":"RETURN strength and suggestions","observed":"return strength, suggestions"}}],"open_defects":[]}}
