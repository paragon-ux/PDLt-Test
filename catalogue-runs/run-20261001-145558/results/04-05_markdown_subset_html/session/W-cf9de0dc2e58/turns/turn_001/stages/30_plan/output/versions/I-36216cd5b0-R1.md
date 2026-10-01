READ the confirmed prompt body
DEFINE Python functions to handle each Markdown feature (Headers, Bold, Italic, Inline code, Links, Unordered lists, Code blocks, Paragraphs)
IMPLEMENT a line‑based parser that tokenizes the input markdown text
FOR each line DETERMINE its element type (header, list item, code block delimiter, or paragraph) and APPLY the corresponding conversion function
IF a line begins a code block THEN COLLECT subsequent lines until the closing delimiter and WRAP them in <pre><code> tags
IF a line starts an unordered list item THEN GROUP consecutive list items, CONVERT each to <li> tags, and WRAP the group in <ul> tags
FOR inline elements within a line REPLACE markdown markers with the appropriate HTML tags (**bold**, *italic*, `code`, [link](url))
ASSEMBLE the converted lines into the final HTML document
WRITE a test suite with at least ten distinct markdown inputs covering all features, nested formatting, and edge cases such as empty headers and links with special characters
EXECUTE the test suite to ensure the converter produces the expected HTML output
