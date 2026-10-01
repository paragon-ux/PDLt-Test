import re
import html

class MarkdownConverter:
    def __init__(self):
        self.block_parsers = [
            self.parse_header,
            self.parse_fenced_code,
            self.parse_indented_code,
            self.parse_unordered_list,
            self.parse_paragraph,
        ]
        self.inline_patterns = [
            (re.compile(r"\*\*(.+?)\*\*|__(.+?)__"), self.replace_bold),
            (re.compile(r"\*(.+?)\*|_(.+?)_"), self.replace_italic),
            (re.compile(r"`([^`]+?)`"), self.replace_code),
            (re.compile(r"\[([^\]]+?)\]\(([^)]+?)\)"), self.replace_link),
        ]

    def convert(self, markdown: str) -> str:
        lines = markdown.splitlines()
        i = 0
        html_parts = []
        while i < len(lines):
            for parser in self.block_parsers:
                result, consumed = parser(lines, i)
                if consumed:
                    html_parts.append(result)
                    i += consumed
                    break
            else:
                # fallback: treat as paragraph
                result, consumed = self.parse_paragraph(lines, i)
                html_parts.append(result)
                i += consumed
        return "\n".join(html_parts)

    # ----- Block parsers -------------------------------------------------
    def parse_header(self, lines, i):
        line = lines[i]
        m = re.match(r"^(#{1,6})\s*(.*)$", line)
        if not m:
            return "", 0
        level = len(m.group(1))
        content = self.process_inline(m.group(2).strip())
        return f"<h{level}>{content}</h{level}>", 1

    def parse_fenced_code(self, lines, i):
        if not lines[i].startswith("```"):
            return "", 0
        fence = lines[i]
        i += 1
        code_lines = []
        while i < len(lines) and not lines[i].startswith("```"):
            code_lines.append(lines[i])
            i += 1
        # skip closing fence
        i += 1
        code = "\n".join(code_lines)
        escaped = html.escape(code)
        return f"<pre><code>{escaped}\n</code></pre>", i - (i - len(code_lines) - 2)

    def parse_indented_code(self, lines, i):
        if not lines[i].startswith("    "):
            return "", 0
        code_lines = []
        while i < len(lines) and (lines[i].startswith("    ") or lines[i].strip() == ""):
            code_lines.append(lines[i][4:] if lines[i].startswith("    ") else "")
            i += 1
        code = "\n".join(code_lines)
        escaped = html.escape(code)
        return f"<pre><code>{escaped}\n</code></pre>", len(code_lines)

    def parse_unordered_list(self, lines, i):
        if not re.match(r"^[\*-]\s+", lines[i]):
            return "", 0
        items = []
        while i < len(lines) and re.match(r"^[\*-]\s+", lines[i]):
            marker, rest = lines[i][0], lines[i][1:].lstrip()
            items.append(self.process_inline(rest))
            i += 1
        lis = "\n".join(f"<li>{item}</li>" for item in items)
        return f"<ul>\n{lis}\n</ul>", len(items)

    def parse_paragraph(self, lines, i):
        para_lines = []
        while i < len(lines) and lines[i].strip() != "":
            # stop if next line looks like a block start
            if re.match(r"^(#{1,6})\s|```|[\*-]\s", lines[i]):
                break
            para_lines.append(lines[i])
            i += 1
        content = self.process_inline(" ".join(para_lines).strip())
        return f"<p>{content}</p>", len(para_lines)

    # ----- Inline processing ---------------------------------------------
    def process_inline(self, text: str) -> str:
        # Escape HTML special chars first
        text = html.escape(text)
        # Apply patterns repeatedly until no change (handles nesting)
        changed = True
        while changed:
            changed = False
            for pattern, replacer in self.inline_patterns:
                new_text, count = pattern.subn(replacer, text)
                if count:
                    text = new_text
                    changed = True
        return text

    def replace_bold(self, match):
        inner = match.group(1) or match.group(2)
        return f"<strong>{inner}</strong>"

    def replace_italic(self, match):
        inner = match.group(1) or match.group(2)
        return f"<em>{inner}</em>"

    def replace_code(self, match):
        code = html.escape(match.group(1))
        return f"<code>{code}</code>"

    def replace_link(self, match):
        text, url = match.group(1), match.group(2)
        # Escape URL quotes and &, <, >
        esc_url = html.escape(url, quote=True)
        return f"<a href=\"{esc_url}\">{text}</a>"

# ------------------- Test Suite ----------------------------------------
import unittest

class TestMarkdownConverter(unittest.TestCase):
    def setUp(self):
        self.conv = MarkdownConverter()

    def assertMD(self, md, expected_html):
        self.assertEqual(self.conv.convert(md).strip(), expected_html.strip())

    def test_headers(self):
        self.assertMD("# Header1", "<h1>Header1</h1>")
        self.assertMD("## Header2", "<h2>Header2</h2>")
        self.assertMD("###### H6", "<h6>H6</h6>")
        self.assertMD("# ", "<h1></h1>")

    def test_bold_italic(self):
        self.assertMD("**bold**", "<p><strong>bold</strong></p>")
        self.assertMD("__bold2__", "<p><strong>bold2</strong></p>")
        self.assertMD("*italic*", "<p><em>italic</em></p>")
        self.assertMD("_italic2_", "<p><em>italic2</em></p>")
        self.assertMD("*italic **bold inside** italic*", "<p><em>italic <strong>bold inside</strong> italic</em></p>")
        self.assertMD("**bold _italic inside_ bold**", "<p><strong>bold <em>italic inside</em> bold</strong></p>")

    def test_inline_code(self):
        self.assertMD("`code`", "<p><code>code</code></p>")
        self.assertMD("`a < b & c`", "<p><code>a &lt; b &amp; c</code></p>")

    def test_links(self):
        self.assertMD("[Google](https://www.google.com)", "<p><a href=\"https://www.google.com\">Google</a></p>")
        self.assertMD("[Strange](https://example.com?arg=1&b=2)", "<p><a href=\"https://example.com?arg=1&amp;b=2\">Strange</a></p>")

    def test_unordered_list(self):
        md = "- item1\n- item2"
        html = "<ul>\n<li>item1</li>\n<li>item2</li>\n</ul>"
        self.assertMD(md, html)
        md2 = "* a\n* b"
        self.assertMD(md2, html)

    def test_code_blocks(self):
        md = "```\nline1\nline2\n```"
        html = "<pre><code>line1\nline2\n\n</code></pre>"
        self.assertMD(md, html)
        md2 = "    indented line1\n    indented line2"
        self.assertMD(md2, html)

    def test_paragraphs(self):
        md = "First line\nSecond line"
        html = "<p>First line Second line</p>"
        self.assertMD(md, html)

    def test_mixed(self):
        md = "# Title\n\n- **Bold Item**\n- *Italic Item*\n\nParagraph with [link](https://example.com) and `code`."
        html = """<h1>Title</h1>
<ul>
<li><strong>Bold Item</strong></li>
<li><em>Italic Item</em></li>
</ul>
<p>Paragraph with <a href=\"https://example.com\">link</a> and <code>code</code>.</p>"""
        self.assertMD(md, html)

if __name__ == "__main__":
    unittest.main()
