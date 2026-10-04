"""Hidden tests for 04-05: a Markdown-subset to HTML converter.

From the prompt:
- headers # to ######;
- bold (**, __), italic (*, _), inline code, links;
- unordered lists (- or *);
- code blocks (indented four spaces, or fenced);
- paragraphs for consecutive non-blank lines;
- nested formatting (bold inside italic), empty headers, and links with
  special characters.

The prompt's text lost its backticks; inline code and fences are read as
standard Markdown backticks.

HTML is compared as a normalized tree, not as text:
- b/strong and i/em are equivalent;
- only a link's href attribute counts;
- whitespace collapses outside <pre>, and surrounding blank text is ignored;
- a <code> directly inside <pre> is optional;
- entity escaping does not matter (the parser decodes it);
- html, head and body wrappers are ignored.

The entry point is a one-argument function, or a class used as
Class().method(text) or Class(text).method().
"""
TEST_SECONDS = 20
_NAMES = ("markdown_to_html", "convert", "md_to_html", "render", "to_html", "markdown", "parse", "convert_markdown",
          "render_markdown", "md2html", "transform")


def CANDIDATES():
    named = list(functions_named(*_NAMES))
    methods = [_method_adapter(cls, m) for cls in classes_with() for m in _NAMES if callable(getattr(cls, m, None))]
    others = [f for f in functions_named(*_NAMES, params=1) if f not in named]
    return named + methods + others


def _method_adapter(cls, method):
    def convert(text):
        try:
            obj = cls()
        except TypeError:
            return getattr(cls(text), method)()
        try:
            return getattr(obj, method)(text)
        except TypeError:
            return getattr(cls(text), method)()

    convert.__name__ = f"{cls.__name__}.{method}"
    return convert


_BLOCK = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "pre", "div", "blockquote", "hr"}
_ALIAS = {"b": "strong", "i": "em"}
_SKIP = {"html", "head", "body"}


def _normalize(html):
    from html.parser import HTMLParser

    tokens = []

    class Collect(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.pre = 0

        def handle_starttag(self, tag, attrs):
            tag = _ALIAS.get(tag, tag)
            if tag in _SKIP or (tag == "code" and self.pre):
                return
            if tag == "pre":
                self.pre += 1
            href = dict(attrs).get("href") if tag == "a" else None
            tokens.append(("open", tag, href))

        def handle_endtag(self, tag):
            tag = _ALIAS.get(tag, tag)
            if tag in _SKIP or (tag == "code" and self.pre):
                return
            if tag == "pre":
                self.pre = max(0, self.pre - 1)
            tokens.append(("close", tag, None))

        def handle_data(self, data):
            if tokens and tokens[-1][0] == "text":
                tokens[-1] = ("text", tokens[-1][1] + data, tokens[-1][2])
            else:
                tokens.append(("text", data, self.pre > 0))

    Collect().feed(html)
    out = []
    for i, (kind, value, extra) in enumerate(tokens):
        if kind != "text":
            out.append((kind, value, extra))
            continue
        if extra:  # inside <pre>: exact, minus surrounding newlines
            out.append(("text", value.strip("\n").rstrip(), None))
            continue
        import re

        text = re.sub(r"\s+", " ", value)
        prev = tokens[i - 1] if i > 0 else None
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        if prev is None or prev[1] in _BLOCK:
            text = text.lstrip()
        if nxt is None or nxt[1] in _BLOCK:
            text = text.rstrip()
        if text:
            out.append(("text", text, None))
    return out


def _check(f, markdown, expected):
    got = f(markdown)
    assert isinstance(got, str), f"{markdown!r} gave {type(got).__name__}"
    assert _normalize(got) == _normalize(expected), f"{markdown!r}\n got:      {got!r}\n expected: {expected!r}"


def test_headers(f):
    _check(f, "# Title", "<h1>Title</h1>")
    _check(f, "### Three", "<h3>Three</h3>")
    _check(f, "###### Six", "<h6>Six</h6>")
    _check(f, "## Mixed **bold** here", "<h2>Mixed <strong>bold</strong> here</h2>")
    _check(f, "# ", "<h1></h1>")


def test_inline_formatting(f):
    _check(f, "**bold** and __also bold__", "<p><strong>bold</strong> and <strong>also bold</strong></p>")
    _check(f, "*it* and _also it_", "<p><em>it</em> and <em>also it</em></p>")
    _check(f, "use `x = 1` now", "<p>use <code>x = 1</code> now</p>")
    _check(f, "`*not italic*` stays", "<p><code>*not italic*</code> stays</p>")


def test_nested_formatting(f):
    _check(f, "*italic **bold** inside*", "<p><em>italic <strong>bold</strong> inside</em></p>")
    _check(f, "**bold *italic* inside**", "<p><strong>bold <em>italic</em> inside</strong></p>")


def test_links(f):
    _check(f, "see [the docs](http://example.com/page)", '<p>see <a href="http://example.com/page">the docs</a></p>')
    _check(f, "[q](http://x.com/a_b_c?q=1&r=2)", '<p><a href="http://x.com/a_b_c?q=1&amp;r=2">q</a></p>')
    _check(f, "[**bold** link](http://x.com)", '<p><a href="http://x.com"><strong>bold</strong> link</a></p>')


def test_lists(f):
    _check(f, "- one\n- two\n- three", "<ul><li>one</li><li>two</li><li>three</li></ul>")
    _check(f, "* alpha\n* *beta*", "<ul><li>alpha</li><li><em>beta</em></li></ul>")


def test_code_blocks(f):
    _check(f, "    code *not* em\n    second line", "<pre><code>code *not* em\nsecond line</code></pre>")
    _check(f, "```\nfenced **raw**\n  indented\n```", "<pre><code>fenced **raw**\n  indented</code></pre>")
    _check(f, "```python\nx = [1, 2]\n```", "<pre><code>x = [1, 2]</code></pre>")


def test_paragraphs_and_documents(f):
    _check(f, "line one\nline two\n\nsecond para", "<p>line one line two</p><p>second para</p>")
    _check(f, "# Head\n\nSome *text*.\n\n- a\n- b\n\nEnd.",
           "<h1>Head</h1><p>Some <em>text</em>.</p><ul><li>a</li><li>b</li></ul><p>End.</p>")


TESTS = [test_headers, test_inline_formatting, test_nested_formatting, test_links, test_lists, test_code_blocks,
         test_paragraphs_and_documents]
