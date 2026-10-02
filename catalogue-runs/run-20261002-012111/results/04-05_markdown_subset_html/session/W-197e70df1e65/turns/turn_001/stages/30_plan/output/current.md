PARSE the markdown source into lines
DETERMINE block boundaries (headers, code blocks, lists, paragraphs)
FOR each line
  IF line matches header syntax with 1–6 leading '#'
    CONVERT to the corresponding <h1>–<h6> tag
  ELSE IF line matches fenced code block delimiter (``` ) OR four‑space indentation
    COLLECT code block content
    WRAP in <pre><code> tags
  ELSE IF line matches unordered list marker '-' OR '*'
    GROUP consecutive list items
    WRAP in <ul> and <li> tags
  ELSE
    TREAT as normal paragraph text
    WRAP in <p> tags after processing inline formatting
PROCESS inline formatting within each block
  REPLACE **text** and __text__ with <strong>text</strong>
  REPLACE *text* and _text_ with <em>text</em>
  REPLACE `code` with <code>code</code>
  REPLACE [text](url) with <a href="url">text</a>
  HANDLE nested formatting by applying replacements without overlap
ASSEMBLE all converted blocks into the final HTML document string
CREATE a test suite with at least ten markdown strings covering header levels, bold, italic, nested formatting, inline code, links with special characters, unordered lists with '-' and '*', code blocks via indentation and fences, paragraph wrapping, and edge cases such as empty headers
FOR each test case
  EXECUTE the conversion program on the markdown input
  COMPARE the generated HTML to the expected HTML for that case
  RECORD success or failure
REPORT that all tests must pass before final delivery
ENSURE the implementation uses only Python's standard library and does not import external packages
