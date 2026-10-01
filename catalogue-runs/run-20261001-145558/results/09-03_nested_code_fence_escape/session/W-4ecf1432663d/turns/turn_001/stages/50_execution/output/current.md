def format_code_block(code: str) -> str:
    """Return a markdown code block with the given code string escaped.

    The function:
    1. Escapes backslashes ("\\") by doubling them.
    2. Escapes any backticks ("`") by prefixing them with a backslash.
    3. Detects raw triple backticks inside the string and escapes them so they do not close the outer fence.
    4. Wraps the escaped string in a markdown fenced code block using triple backticks.
    """
    # Step 1: escape backslashes
    escaped = code.replace('\\', '\\\\')
    # Step 2: escape backticks
    escaped = escaped.replace('`', '\`')
    # Step 3: escape any occurrence of three consecutive escaped backticks ("\`\`\`")
    # This would otherwise form a closing fence when the outer fence is unescaped.
    escaped = escaped.replace('\`\`\`', '\`\\`\`')
    # Wrap in triple backticks
    return f"```\n{escaped}\n```"

# Test suite
if __name__ == "__main__":
    import unittest

    class TestFormatCodeBlock(unittest.TestCase):
        def test_single_backticks(self):
            inp = "print('Hello `world`')"
            out = format_code_block(inp)
            self.assertTrue(out.startswith('```'))
            self.assertIn("\`", out)
            self.assertNotIn('```\n', out[4:])  # inner triple backticks should not appear

        def test_backslashes(self):
            inp = r"path = 'C:\\Users\\test'"
            out = format_code_block(inp)
            self.assertIn('\\\\', out)  # each backslash doubled twice
            self.assertTrue(out.endswith('```'))

        def test_raw_triple_backticks(self):
            inp = "some text ``` inside code"
            out = format_code_block(inp)
            # The raw triple backticks should be escaped and not terminate the block
            self.assertNotIn('```\nsome text ``` inside code\n```', out)
            self.assertIn('\`\`\`', out)  # escaped version appears

        def test_nested_backticks(self):
            inp = "def f():\n    return '`nested`'"
            out = format_code_block(inp)
            self.assertIn('\`nested\`', out)
            self.assertTrue(out.startswith('```'))
            self.assertTrue(out.endswith('```'))

    unittest.main(argv=['first-arg-is-ignored'], exit=False)
