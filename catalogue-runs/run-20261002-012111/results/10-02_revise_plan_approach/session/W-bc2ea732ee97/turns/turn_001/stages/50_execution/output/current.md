def extract_links(html: str) -> list:
    """Extract all hyperlink URLs from the given HTML string.

    Args:
        html: A string containing the HTML content.
    Returns:
        A list of strings, each being the value of an href attribute from an <a> tag.
    """
    from html.parser import HTMLParser

    class LinkExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
        def handle_starttag(self, tag, attrs):
            if tag.lower() == "a":
                for attr, value in attrs:
                    if attr.lower() == "href" and value is not None:
                        self.links.append(value)
                        break
    parser = LinkExtractor()
    parser.feed(html)
    return parser.links
