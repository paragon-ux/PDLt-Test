# Wrong: a recursive backtracking matcher over the parse tree. Its answers are
# right, but it is not an NFA simulation and takes exponential time on (a|a)*b.
def _parse(p):
    pos = [0]

    def peek():
        return p[pos[0]] if pos[0] < len(p) else None

    def alt():
        branches = [seq()]
        while peek() == "|":
            pos[0] += 1
            branches.append(seq())
        return ("alt", branches)

    def seq():
        items = []
        while peek() not in (None, "|", ")"):
            items.append(rep())
        return ("seq", items)

    def rep():
        node = atom()
        while peek() in ("*", "+", "?"):
            node = (p[pos[0]], node)
            pos[0] += 1
        return node

    def atom():
        c = peek()
        if c == "(":
            pos[0] += 1
            node = alt()
            pos[0] += 1
            return node
        if c == "[":
            end = p.index("]", pos[0])
            body = p[pos[0] + 1:end]
            pos[0] = end + 1
            return ("cls", body)
        pos[0] += 1
        return ("chr", c)

    return alt()


def _m(node, s, i, k):
    kind = node[0]
    if kind == "chr":
        return i < len(s) and (node[1] == "." or s[i] == node[1]) and k(i + 1)
    if kind == "cls":
        body, ok = node[1], False
        if i < len(s):
            j = 0
            while j < len(body):
                if j + 2 < len(body) and body[j + 1] == "-":
                    ok = ok or body[j] <= s[i] <= body[j + 2]
                    j += 3
                else:
                    ok = ok or s[i] == body[j]
                    j += 1
        return ok and k(i + 1)
    if kind == "seq":
        def run(n, j):
            return k(j) if n == len(node[1]) else _m(node[1][n], s, j, lambda j2: run(n + 1, j2))
        return run(0, i)
    if kind == "alt":
        return any(_m(b, s, i, k) for b in node[1])
    if kind == "?":
        return _m(node[1], s, i, k) or k(i)
    if kind == "*":
        return _m(node[1], s, i, lambda j: j > i and _m(node, s, j, k)) or k(i)
    if kind == "+":
        return _m(node[1], s, i, lambda j: _m(("*", node[1]), s, j, k))


def match(pattern, text):
    return _m(_parse(pattern), text, 0, lambda j: j == len(text))
