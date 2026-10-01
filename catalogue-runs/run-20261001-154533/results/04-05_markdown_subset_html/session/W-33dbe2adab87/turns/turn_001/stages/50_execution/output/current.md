import re
import sys
from typing import List

class MarkdownConverter:
    def __init__(self):
        self.inline_patterns = [
            (re.compile(r'\*\*(.+?)\*\*'), r'<strong>\1</strong>'),
            (re.compile(r'__(.+?)__'), r'<strong>\1</strong>'),
            (re.compile(r'\*(.+?)\*'), r'<em>\1</em>'),
            (re.compile(r'_(.+?)_'), r'<em>\1</em>'),
            (re.compile(r'`(.+?)`'), r'<code>\1</code>'),
            (re.compile(r'\[(.+?)\]\((.+?)\)'), r'<a href="\2">\1</a>'),
        ]

    def replace_inline(self, text: str) -> str:
        for pattern, repl in self.inline_patterns:
            text = pattern.sub(repl, text)
        return text

    def convert(self, markdown: str) -> str:
        lines = markdown.split('\n')
        html_blocks: List[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Header
            header_match = re.match(r'^(#{1,6})\s*(.*)$', line)
            if header_match:
                level = len(header_match.group(1))
                content = self.replace_inline(header_match.group(2).strip())
                html_blocks.append(f'<h{level}>{content}</h{level}>')
                i += 1
                continue
            # Fenced code block
            if line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # skip closing fence
                code_html = '\n'.join(self.replace_inline('\n'.join(code_lines)))
                html_blocks.append(f'<pre><code>{code_html}</code></pre>')
                continue
            # Indented code block (4 spaces)
            if line.startswith('    '):
                code_lines = []
                while i < len(lines) and lines[i].startswith('    '):
                    code_lines.append(lines[i][4:])
                    i += 1
                code_html = '\n'.join(self.replace_inline('\n'.join(code_lines)))
                html_blocks.append(f'<pre><code>{code_html}</code></pre>')
                continue
            # Unordered list
            if re.match(r'^[\*-]\s+', line):
                items = []
                while i < len(lines) and re.match(r'^[\*-]\s+', lines[i]):
                    item_content = re.sub(r'^[\*-]\s+', '', lines[i])
                    item_content = self.replace_inline(item_content)
                    items.append(f'<li>{item_content}</li>')
                    i += 1
                html_blocks.append('<ul>' + ''.join(items) + '</ul>')
                continue
            # Paragraph
            if line.strip() != '':
                para_lines = []
                while i < len(lines) and lines[i].strip() != '':
                    para_lines.append(self.replace_inline(lines[i]))
                    i += 1
                html_blocks.append(f'<p>{" ".join(para_lines)}</p>')
                continue
            # Blank line
            i += 1
        return '\n'.join(html_blocks)

# Test suite
import unittest

class TestMarkdownConverter(unittest.TestCase):
    def setUp(self):
        self.conv = MarkdownConverter()

    def test_headers(self):
        md = "# H1\n## H2\n###### H6"
        html = self.conv.convert(md)
        self.assertIn('<h1>H1</h1>', html)
        self.assertIn('<h2>H2</h2>', html)
        self.assertIn('<h6>H6</h6>', html)

    def test_bold(self):
        md = "**bold** and __also bold__"
        html = self.conv.convert(md)
        self.assertIn('<strong>bold</strong>', html)
        self.assertIn('<strong>also bold</strong>', html)

    def test_italic(self):
        md = "*italic* and _also italic_"
        html = self.conv.convert(md)
        self.assertIn('<em>italic</em>', html)
        self.assertIn('<em>also italic</em>', html)

    def test_inline_code(self):
        md = "This is `code` inside."
        html = self.conv.convert(md)
        self.assertIn('<code>code</code>', html)

    def test_links(self):
        md = "[OpenAI](https://openai.com)"
        html = self.conv.convert(md)
        self.assertIn('<a href="https://openai.com">OpenAI</a>', html)

    def test_unordered_list(self):
        md = "- item1\n* item2"
        html = self.conv.convert(md)
        self.assertIn('<ul><li>item1</li><li>item2</li></ul>', html)

    def test_code_blocks_fenced(self):
        md = "```\nline1\nline2\n```"
        html = self.conv.convert(md)
        self.assertIn('<pre><code>line1\nline2</code></pre>', html)

    def test_code_blocks_indented(self):
        md = "    line1\n    line2"
        html = self.conv.convert(md)
        self.assertIn('<pre><code>line1\nline2</code></pre>', html)

    def test_paragraphs(self):
        md = "First line\nSecond line\n\nNew paragraph"
        html = self.conv.convert(md)
        self.assertIn('<p>First line Second line</p>', html)
        self.assertIn('<p>New paragraph</p>', html)

    def test_nested_formatting(self):
        md = "**bold and *italic inside***"
        html = self.conv.convert(md)
        self.assertIn('<strong>bold and <em>italic inside</em></strong>', html)

    def test_edge_cases(self):
        md = "#   \n[link](mailto:test@example.com?subject=Hello%20World)"
        html = self.conv.convert(md)
        self.assertIn('<h1></h1>', html)
        self.assertIn('<a href="mailto:test@example.com?subject=Hello%20World">link</a>', html)

if __name__ == '__main__':
    unittest.main()
