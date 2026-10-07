# Wrong: link markup is not protected from the emphasis passes, so underscores
# in a URL turn into italics.
import re


class MarkdownConverter:
    def render(self, text):
        blocks, para, lines, i = [], [], text.splitlines(), 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("```"):
                self._para(blocks, para)
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("```"):
                    j += 1
                blocks.append("<pre>" + self._esc("\n".join(lines[i + 1:j])) + "</pre>")
                i = j + 1
            elif line.startswith("    ") and not para:
                j = i
                while j < len(lines) and lines[j].startswith("    "):
                    j += 1
                blocks.append("<pre>" + self._esc("\n".join(l[4:] for l in lines[i:j])) + "</pre>")
                i = j
            elif re.match(r"#{1,6}(\s|$)", line):
                self._para(blocks, para)
                hashes = len(line) - len(line.lstrip("#"))
                blocks.append(f"<h{hashes}>{self._inline(line[hashes:].strip())}</h{hashes}>")
                i += 1
            elif re.match(r"[-*]\s", line):
                self._para(blocks, para)
                items = []
                while i < len(lines) and re.match(r"[-*]\s", lines[i]):
                    items.append(f"  <li>{self._inline(lines[i][2:].strip())}</li>")
                    i += 1
                blocks.append("<ul>\n" + "\n".join(items) + "\n</ul>")
            elif not line.strip():
                self._para(blocks, para)
                i += 1
            else:
                para.append(line)
                i += 1
        self._para(blocks, para)
        return "\n\n".join(blocks) + "\n"

    def _para(self, blocks, para):
        if para:
            blocks.append("<p>" + self._inline("\n".join(para)) + "</p>")
            para.clear()

    @staticmethod
    def _esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _inline(self, s):
        saved = []

        def keep(html):
            saved.append(html)
            return f"\x00{len(saved) - 1}\x00"

        s = self._esc(s)
        s = re.sub(r"`([^`]+)`", lambda m: keep(f"<code>{m.group(1)}</code>"), s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   lambda m: f'<a href="{m.group(2)}">' + m.group(1) + "</a>", s)
        s = re.sub(r"(\*\*|__)(.+?)\1", r"<b>\2</b>", s)
        s = re.sub(r"(\*|_)(.+?)\1", r"<i>\2</i>", s)
        return re.sub("\x00(\\d+)\x00", lambda m: saved[int(m.group(1))], s)
