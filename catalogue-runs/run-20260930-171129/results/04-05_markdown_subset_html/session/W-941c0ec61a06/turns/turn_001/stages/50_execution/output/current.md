# markdown_converter.py
import re

def escape_html(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

def replace_inline(text):
    # code
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    # bold (** or __)
    text = re.sub(r'(\*\*|__)((?:\\.|[^\\*])+?)\1', r'<strong>\2</strong>', text)
    # italic (* or _)
    text = re.sub(r'(\*|_)((?:\\.|[^\\*_])+?)\1', r'<em>\2</em>', text)
    # links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text

def parse(lines):
    html = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # fenced code block
        if line.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(escape_html(lines[i]))
                i += 1
            html.append('<pre><code>' + "\n".join(code_lines) + '</code></pre>')
            i += 1
            continue
        # indented code block (4 spaces)
        if line.startswith('    '):
            code_lines = []
            while i < len(lines) and lines[i].startswith('    '):
                code_lines.append(escape_html(lines[i][4:]))
                i += 1
            html.append('<pre><code>' + "\n".join(code_lines) + '</code></pre>')
            continue
        # header
        m = re.match(r'^(#{1,6})\s*(.*)$', line)
        if m:
            level = len(m.group(1))
            content = replace_inline(m.group(2).strip())
            html.append(f'<h{level}>{content}</h{level}>')
            i += 1
            continue
        # unordered list
        if re.match(r'^[-*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i]):
                item_text = re.sub(r'^[-*]\s+', '', lines[i])
                items.append('<li>' + replace_inline(item_text) + '</li>')
                i += 1
            html.append('<ul>' + "".join(items) + '</ul>')
            continue
        # paragraph (collect consecutive non‑blank lines)
        if line.strip() != '':
            para_lines = []
            while i < len(lines) and lines[i].strip() != '' and not re.match(r'^(#{1,6})\s|^[-*]\s|^    |^```', lines[i]):
                para_lines.append(lines[i])
                i += 1
            para = replace_inline(' '.join(para_lines).strip())
            html.append('<p>' + para + '</p>')
            continue
        # blank line
        i += 1
    return '\n'.join(html)

def markdown_to_html(md: str) -> str:
    lines = md.replace('\r\n', '\n').split('\n')
    return parse(lines)

# ----------------- tests -----------------
import unittest

class TestMarkdownConverter(unittest.TestCase):
    def test_headers(self):
        md = "# H1\n## H2\n### H3\n#### H4\n##### H5\n###### H6"
        html = markdown_to_html(md)
        expected = "<h1>H1</h1>\n<h2>H2</h2>\n<h3>H3</h3>\n<h4>H4</h4>\n<h5>H5</h5>\n<h6>H6</h6>"
        self.assertEqual(html, expected)
    def test_bold_italic(self):
        md = "This is **bold** and *italic* and __also bold__ and _also italic_."
        html = markdown_to_html(md)
        expected = "<p>This is <strong>bold</strong> and <em>italic</em> and <strong>also bold</strong> and <em>also italic</em>.</p>"
        self.assertEqual(html, expected)
    def test_nested_inline(self):
        md = "**bold and *italic inside bold***"
        html = markdown_to_html(md)
        expected = "<p><strong>bold and <em>italic inside bold</em></strong></p>"
        self.assertEqual(html, expected)
    def test_inline_code(self):
        md = "Use the `print()` function."
        html = markdown_to_html(md)
        expected = "<p>Use the <code>print()</code> function.</p>"
        self.assertEqual(html, expected)
    def test_link(self):
        md = "Link to [OpenAI](https://openai.com)."
        html = markdown_to_html(md)
        expected = "<p>Link to <a href=\"https://openai.com\">OpenAI</a>.</p>"
        self.assertEqual(html, expected)
    def test_unordered_list(self):
        md = "- Item 1\n- Item 2\n* Item 3"
        html = markdown_to_html(md)
        expected = "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
        self.assertEqual(html, expected)
    def test_code_block_fenced(self):
        md = "```\ndef foo():\n    return 1\n```"
        html = markdown_to_html(md)
        expected = "<pre><code>def foo():\n    return 1</code></pre>"
        self.assertEqual(html, expected)
    def test_code_block_indented(self):
        md = "    def bar():\n        return 2"
        html = markdown_to_html(md)
        expected = "<pre><code>def bar():\n    return 2</code></pre>"
        self.assertEqual(html, expected)
    def test_paragraph_wrapping(self):
        md = "First line.\nSecond line."
        html = markdown_to_html(md)
        expected = "<p>First line. Second line.</p>"
        self.assertEqual(html, expected)
    def test_mixed_content(self):
        md = "# Title\n\nParagraph with **bold** and a [link](http://example.com).\n\n- List item with `code`\n- Another item"
        html = markdown_to_html(md)
        expected = "<h1>Title</h1>\n<p>Paragraph with <strong>bold</strong> and a <a href=\"http://example.com\">link</a>.</p>\n<ul><li>List item with <code>code</code></li><li>Another item</li></ul>"
        self.assertEqual(html, expected)

if __name__ == '__main__':
    unittest.main()
