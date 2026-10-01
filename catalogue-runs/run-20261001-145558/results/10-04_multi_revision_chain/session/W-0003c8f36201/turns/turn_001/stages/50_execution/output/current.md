import re

def validate_email(email: str) -> bool:
    """Validate an email address using a regular expression.

    This function checks that the email consists of alphanumeric characters,
    periods, hyphens, and underscores before the ``@`` symbol, followed by a
    valid domain name. The regex is compiled with the ``re.IGNORECASE`` flag
    to allow case‑insensitive matching.

    Example:
        >>> validate_email('user.name@example-domain.com')
        True
        >>> validate_email('invalid-email@')
        False
    """
    pattern = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        re.IGNORECASE,
    )
    return bool(pattern.fullmatch(email))
