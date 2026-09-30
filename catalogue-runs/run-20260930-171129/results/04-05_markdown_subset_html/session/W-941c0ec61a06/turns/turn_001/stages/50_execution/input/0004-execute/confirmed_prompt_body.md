READ the request to implement a Markdown-to-HTML converter in Python
SUPPORT conversion of headers (# through ######) to corresponding <h1>–<h6> tags
SUPPORT bold formatting using **text** and __text** to <strong> tags
SUPPORT italic formatting using *text* and _text_ to <em> tags
SUPPORT inline code delimited by `code` to <code> tags
SUPPORT links of the form [text](url) to <a href="url">text</a> tags
SUPPORT unordered lists where lines start with - or * to <ul><li>...</li></ul> structures
SUPPORT code blocks indicated by 4-space indentation or fenced with ``` to <pre><code>...</code></pre> tags
WRAP consecutive non-blank lines that are not otherwise formatted in <p> tags
DO NOT use any external libraries
PROVIDE at least ten tests that cover all supported features, including nested formatting and edge cases
