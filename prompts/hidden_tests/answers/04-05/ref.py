import html
import re

_HEADER = re.compile(r"^(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_ITEM = re.compile(r"^[-*][ \t]+(.*)$")


def _find_single(text, start, ch):
    """Index of the closing single delimiter, skipping doubled ones."""
    j = start
    while j < len(text):
        if text.startswith(ch * 2, j):
            close = text.find(ch * 2, j + 2)
            if close < 0:
                return -1
            j = close + 2
            continue
        if text[j] == ch:
            return j
        j += 1
    return -1


def inline(text):
    out, i = [], 0
    while i < len(text):
        c = text[i]
        if c == "`":
            end = text.find("`", i + 1)
            if end > i:
                out.append("<code>" + html.escape(text[i + 1:end], quote=False) + "</code>")
                i = end + 1
                continue
        if c == "[":
            m = re.match(r"\[([^\]]*)\]\(([^)\s]*)\)", text[i:])
            if m:
                out.append('<a href="' + html.escape(m.group(2)) + '">' + inline(m.group(1)) + "</a>")
                i += m.end()
                continue
        if c in "*_" and text.startswith(c * 2, i):
            end = text.find(c * 2, i + 2)
            if end > i + 2:
                out.append("<strong>" + inline(text[i + 2:end]) + "</strong>")
                i = end + 2
                continue
        if c in "*_":
            end = _find_single(text, i + 1, c)
            if end > i + 1:
                out.append("<em>" + inline(text[i + 1:end]) + "</em>")
                i = end + 1
                continue
        out.append(html.escape(c, quote=False))
        i += 1
    return "".join(out)


def markdown_to_html(source):
    lines = source.split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(s.strip() for s in para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush()
            body, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(body), quote=False) + "</code></pre>")
            i += 1
            continue
        if line.startswith("    ") and not para:
            body = []
            while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
                body.append(lines[i][4:])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(body).rstrip("\n"), quote=False) + "</code></pre>")
            continue
        header = _HEADER.match(line)
        if header:
            flush()
            level = len(header.group(1))
            out.append(f"<h{level}>" + inline(header.group(2) or "") + f"</h{level}>")
            i += 1
            continue
        if _ITEM.match(line):
            flush()
            items = []
            while i < len(lines) and _ITEM.match(lines[i]):
                items.append("<li>" + inline(_ITEM.match(lines[i]).group(1)) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if not line.strip():
            flush()
        else:
            para.append(line)
        i += 1
    flush()
    return "\n".join(out)
