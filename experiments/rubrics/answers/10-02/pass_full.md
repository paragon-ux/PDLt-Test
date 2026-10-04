```python
from html.parser import HTMLParser
from urllib.request import urlopen

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

def extract_links(html: str) -> list[str]:
    parser = LinkExtractor()
    parser.feed(html)
    return parser.links

def links_from_url(url: str) -> list[str]:
    with urlopen(url) as resp:
        return extract_links(resp.read().decode(resp.headers.get_content_charset() or "utf-8"))
```
