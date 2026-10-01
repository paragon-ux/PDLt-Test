READ markdown source
PARSE lines into block tokens
CLASSIFY each block as HEADER, LIST, PARAGRAPH, CODE_BLOCK, or OTHER
FOR EACH block DO
    IF block is HEADER THEN
        MAP header level markers (# through ######) to <h1>..</h1> tags
    ELSE IF block is UNORDERED LIST THEN
        MAP list items prefixed with - or * to <ul><li>..</li></ul>
    ELSE IF block is CODE_BLOCK THEN
        DETECT indentation of 4 spaces OR fenced backticks and WRAP content in <pre><code> tags
    ELSE IF block is PARAGRAPH THEN
        WRAP consecutive non-blank lines in <p> tags
    ENDIF
    PROCESS inline markup within block:
        REPLACE **text** or __text__ with <strong>text</strong>
        REPLACE *text* or _text_ with <em>text</em>
        REPLACE `code` with <code>code</code>
        REPLACE [text](url) with <a href="url">text</a>
    ENSURE nesting of inline elements is preserved
ENDFOR
EMIT concatenated HTML as final output
GENERATE test suite
DEFINE at least ten test cases covering all listed features
INCLUDE nested formatting cases (e.g., bold inside italic)
INCLUDE edge cases such as empty headers and links with special characters
RUN tests to verify generated HTML matches expected results
