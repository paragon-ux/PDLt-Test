WRITE a Python program that converts Markdown text to HTML without using any external libraries. The program MUST support:
- HEADER syntax for levels 1 to 6 using # through ######.
- BOLD formatting using **text** and __text__.
- ITALIC formatting using *text* and _text_.
- INLINE CODE delimited by backticks `code`.
- LINKS formatted as [text](url).
- UNORDERED LISTS where items start with - or *.
- CODE BLOCKS indicated by four-space indentation or fenced with backticks.
- PARAGRAPHS that wrap consecutive non-blank lines in <p> tags.
PROVIDE a test suite containing at least 10 distinct Markdown test strings covering all listed features, including nested formatting cases such as bold inside italic, and edge cases like empty headers and links with special characters.
