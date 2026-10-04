# Correct with a different interface: Regex(pattern).accepts(text), built from a
# shunting-yard postfix form with an explicit concatenation operator; states are
# integers in transition tables.
EPS = None


class Regex:
    def __init__(self, pattern):
        self.trans = []          # trans[state] = list of (label, target); label is EPS, ".", a char or a set
        self.start, self.accept = self._build(self._postfix(self._tokens(pattern)))

    @staticmethod
    def _tokens(pattern):
        out, i = [], 0
        while i < len(pattern):
            c = pattern[i]
            if c == "[":
                j = pattern.index("]", i)
                body, chars, k = pattern[i + 1:j], set(), 0
                while k < len(body):
                    if k + 2 < len(body) and body[k + 1] == "-":
                        chars |= {chr(x) for x in range(ord(body[k]), ord(body[k + 2]) + 1)}
                        k += 3
                    else:
                        chars.add(body[k])
                        k += 1
                out.append(("lit", frozenset(chars)))
                i = j + 1
                continue
            out.append(("op", c) if c in "|*+?()" else ("lit", "." if c == "." else c))
            i += 1
        # Insert explicit concatenation "&" between adjacent operands.
        result = []
        for tok in out:
            if result:
                prev = result[-1]
                left = prev[0] == "lit" or prev[1] in (")", "*", "+", "?")
                right = tok[0] == "lit" or tok[1] == "("
                if left and right:
                    result.append(("op", "&"))
            result.append(tok)
        return result

    @staticmethod
    def _postfix(tokens):
        prec = {"|": 1, "&": 2}
        out, ops = [], []
        for kind, val in tokens:
            if kind == "lit" or val in "*+?":
                out.append((kind, val))
            elif val == "(":
                ops.append(val)
            elif val == ")":
                while ops[-1] != "(":
                    out.append(("op", ops.pop()))
                ops.pop()
            else:
                while ops and ops[-1] != "(" and prec[ops[-1]] >= prec[val]:
                    out.append(("op", ops.pop()))
                ops.append(val)
        while ops:
            out.append(("op", ops.pop()))
        return out

    def _new(self):
        self.trans.append([])
        return len(self.trans) - 1

    def _build(self, postfix):
        stack = []
        for kind, val in postfix:
            if kind == "lit":
                s, a = self._new(), self._new()
                self.trans[s].append((val, a))
                stack.append((s, a))
            elif val == "&":
                (s2, a2), (s1, a1) = stack.pop(), stack.pop()
                self.trans[a1].append((EPS, s2))
                stack.append((s1, a2))
            elif val == "|":
                (s2, a2), (s1, a1) = stack.pop(), stack.pop()
                s, a = self._new(), self._new()
                self.trans[s] += [(EPS, s1), (EPS, s2)]
                self.trans[a1].append((EPS, a))
                self.trans[a2].append((EPS, a))
                stack.append((s, a))
            else:
                s1, a1 = stack.pop()
                s, a = self._new(), self._new()
                self.trans[s].append((EPS, s1))
                self.trans[a1].append((EPS, a))
                if val in "*?":
                    self.trans[s].append((EPS, a))
                if val in "*+":
                    self.trans[a1].append((EPS, s1))
                stack.append((s, a))
        return stack.pop()

    def _eclose(self, states):
        todo, seen = list(states), set(states)
        while todo:
            for label, t in self.trans[todo.pop()]:
                if label is EPS and t not in seen:
                    seen.add(t)
                    todo.append(t)
        return seen

    def accepts(self, text):
        cur = self._eclose({self.start})
        for ch in text:
            nxt = set()
            for s in cur:
                for label, t in self.trans[s]:
                    if label is EPS:
                        continue
                    if label == "." or label == ch or (isinstance(label, frozenset) and ch in label):
                        nxt.add(t)
            cur = self._eclose(nxt)
        return self.accept in cur
