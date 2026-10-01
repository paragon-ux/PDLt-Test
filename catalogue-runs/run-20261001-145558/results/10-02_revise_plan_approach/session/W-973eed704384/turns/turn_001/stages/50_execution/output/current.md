import re
from html import unescape

def extract_links(html: str) -> list:
    """Extract all hyperlink URLs from the given HTML string.
    Returns a list of URLs as strings. Duplicates are preserved in order of appearance.
    """
    # Simple regex to find href attributes; this works for most cases without full parsing.
    href_pattern = re.compile(r'''href\s*=\s*(['"])(.*?)\1''', re.IGNORECASE)
    urls = []
    for match in href_pattern.finditer(html):
        url = unescape(match.group(2).strip())
        if url:
            urls.append(url)
    return urls

# Example usage (can be removed in production):
if __name__ == "__main__":
    import sys
    html_content = sys.stdin.read()
    links = extract_links(html_content)
    for link in links:
        print(link)
