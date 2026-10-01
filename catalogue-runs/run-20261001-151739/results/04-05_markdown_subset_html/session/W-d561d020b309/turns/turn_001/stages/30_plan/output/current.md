DEFINE the converter architecture
PARSE the raw markdown input into block‑level elements
IDENTIFY block type for each line or group of lines
  IF line starts with 1‑6 "#" characters THEN classify as header block
  ELSE IF line matches a fenced code delimiter or four‑space indentation THEN classify as code block
  ELSE IF line starts with "-" OR "*" THEN classify as unordered list block
  ELSE IF line is non‑blank THEN classify as paragraph block
TOKENIZE block content for inline elements
  RECOGNIZE bold delimiters "**" and "__"
  RECOGNIZE italic delimiters "*" and "_"
  RECOGNIZE inline code delimiters "`"
  RECOGNIZE link patterns "[text](url)"
APPLY transformation rules to map tokens to HTML tags
  MAP header levels to <h1>‑<h6>
  MAP bold to <strong>
  MAP italic to <em>
  MAP inline code to <code>
  MAP links to <a href=\"url\">text</a>
  WRAP paragraphs in <p>
  CONVERT unordered list items to <ul> with <li>
  PRESERVE code block formatting inside <pre><code>
HANDLE nested inline formatting by processing tokens from outermost to innermost
HANDLE edge cases
  TREAT empty header lines as empty header tags
  ESCAPE special characters in URLs
  PRESERVE whitespace inside inline code spans
COMPOSE the final HTML output by concatenating transformed blocks in original order
IMPLEMENT a test suite covering at least ten markdown inputs
  CREATE markdown samples for each required feature and edge case
  FOR each sample CALL the converter and COMPARE the result with the expected HTML
VALIDATE that only the Python standard library is used
