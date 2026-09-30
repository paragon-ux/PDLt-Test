import sys
import re
from html.parser import HTMLParser

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            for name, value in attrs:
                if name.lower() == 'href' and value:
                    self.links.append(value)

def extract_links(html: str):
    """Return a list of href values from all <a> tags in the given HTML string."""
    parser = LinkExtractor()
    parser.feed(html)
    return parser.links

if __name__ == "__main__":
    # Read HTML content from stdin
    html_content = sys.stdin.read()
    urls = extract_links(html_content)
    for url in urls:
        print(url)
