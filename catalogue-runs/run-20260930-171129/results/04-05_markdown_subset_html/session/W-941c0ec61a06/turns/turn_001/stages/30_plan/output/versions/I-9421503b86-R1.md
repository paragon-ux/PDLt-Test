READ the specification for Markdown-to-HTML conversion
PARSE the input Markdown text line by line
IDENTIFY block-level elements (headers, code blocks, lists, paragraphs) using indentation and marker patterns
FOR each header line starting with # characters DETERMINE header level and WRAP the line content in the corresponding <h1>–<h6> tags
FOR each fenced or indented code block CAPTURE the block content and WRAP it in <pre><code>...</code></pre>
FOR each unordered list line beginning with - or * COLLECT consecutive list items, CREATE a <ul> element, and WRAP each item in <li> tags
FOR remaining non‑blank lines that are not part of another block WRAP the lines in <p> tags
WITHIN each block’s textual content APPLY inline formatting:
REPLACE **text** and __text__ patterns with <strong>text</strong>
REPLACE *text* and _text_ patterns with <em>text</em>
REPLACE `code` patterns with <code>code</code>
REPLACE [text](url) patterns with <a href="url">text</a>
HANDLE nesting of inline formats by applying replacements in a order that preserves inner markup
COMPILE the transformed HTML fragments into a single output string
DEVELOP at least ten test cases covering:
header conversion for all six levels
bold, italic, and combined bold‑italic scenarios
inline code and code block conversion (both indented and fenced)
hyperlink rendering
unordered list rendering with multiple items and nested lists
paragraph wrapping of plain text
mixed content combining multiple supported features
edge cases such as empty lines, escaped markup, and malformed syntax
EXECUTE the test suite and VERIFY that each test produces the expected HTML output
