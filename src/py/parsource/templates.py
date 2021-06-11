import re
from typing import Match

RE_SPACES = re.compile(r" +")
RE_SPECIAL = re.compile(r"\\\:\/\?\*\+")
RE_TEMPLATE = re.compile(r"^([A-Z_]+)(:([a-z_]+))?$")


class Node:
    """Nodes are used in the Parsource AST."""

    def __init__(self, type: str, value: str = ""):
        self.type = type
        self.value = value
        self.children = []
        self.parent = None
        self.cardinality = ""

    @property
    def previous(self):
        if self.parent:
            siblings = self.parent.children
            i = siblings.index(self)
            return siblings[i - 1] if i > 0 else None
        else:
            return None

    @property
    def next(self):
        if self.parent:
            siblings = self.parent.children
            i = siblings.index(self)
            return siblings[i + 1] if i < len(siblings) else None
        else:
            return None

    def detach(self):
        if self.parent:
            self.parent.children.remove(self)
            self.parent = None
        return self

    def append(self, child: 'Node'):
        assert isinstance(child, Node)
        self.children.append(child)
        child.parent = self
        return child

    def toRegExp(self):
        """Converts the AST into a regular expression."""
        if self.type == "expr":
            # When we have an (expr…) node, we just recursively
            # convert it to a regexp
            return f"{''.join(_.toRegExp() for _ in self.children)}"
        elif self.type == "tmpl":
            # Here we have a template (tmpl…)
            groups = []
            sep = ""
            for node in self.children:
                if node.type == "text":
                    # If `tmpl` child is a `text`, we need to see if it
                    # matches `{NAME:TYPE?}``
                    text = node.value
                    match = RE_TEMPLATE.match(text)
                    if match:
                        # If it does, great, we can convert it to a named group
                        name = match.group(1)
                        symbol = (match.group(3) or match.group(1)).lower()
                        if symbol not in Template.SYMBOLS:
                            raise ValueError(
                                f"Unsupported symbol '{symbol}' in: {self}")
                        else:
                            groups.append(
                                f"(?P<{name}>{Template.SYMBOLS[symbol]})")
                    else:
                        # Otherwise it's a text, and we just save it as a group
                        groups.append(node.toRegExp())
                elif node.type == "tmpl":
                    # If the node is a nested template, we just append it
                    # as a regexp.
                    groups.append(node.toRegExp())
                elif node.type == "sep":
                    sep = node.toRegExp()
                else:
                    raise ValueError(
                        f"Child '{node.type}' not supported within: {self.type}")
            res = '|'.join(groups)
            if sep:
                res = f"({res}){sep}"
            return f"({res}){self.cardinality}"
        elif self.type == "text":
            # If it's  text node, we escape and sub it
            text = RE_SPECIAL.sub(lambda _: "\\" + _, self.value)
            text = RE_SPACES.sub(r"\\s+", text)
            return text + "".join(_.toRegExp() for _ in self.children)
        elif self.type == "sep":
            return r"\s*" if self.cardinality == "?" else r"\s+"
        else:
            raise NotImplementedError(f"Node type not suported: {self.type}")

    def __repr__(self):
        res = "(" + self.type
        if self.value:
            res += " " + self.value
        if self.children:
            res += " " + " ".join(repr(_) for _ in self.children)
        return res + ")" + self.cardinality


class Template:
    """Templates match parts of a source file. They are used to cherry pick
    parts and regions of a source."""

    SYMBOLS = {
        "name": r"[A-Za-z_][A-Za-z0-9_]*",
        "rest": r".*",
    }

    @classmethod
    def EscapeSpecial(cls, text: str):
        """Escapes the special characters in the given text, using
        `RE_SPECIAL`."""

    @classmethod
    def ToRegexp(cls, text: str) -> str:
        """Rewrites the given template expression as a regular expression. See
        parsource's template syntax for more information."""
        # text = RE_OPTIONAL.sub(lambda _:f"({cls.EscapeSpecial(_.group(1))})?", text)
        # text = RE_TEMPLATE.sub(lambda _:ParseTemplateExpression(_.group(1)), text)
        # text = text.replace("(…)", r"\([^\)]*\)")
        # text = text.replace("{…}", r"\{[^\}]*\}")
        # text = text.replace("[…]", r"\[[^\]]*\]")
        # return f"^\\s*{text}"

        return cls.ParseTemplateExpression(text)

    @classmethod
    def Compile(cls, text, separator=' '):
        return re.compile(cls.Parse(text, separator).toRegExp())

    @classmethod
    def Parse(cls, text, separator=' ') -> str:
        # return f"(?P<{name}>{cls.SYMBOLS[typename[1:]]})"
        o = 0
        n = len(text)
        root = Node("expr")
        current: Node = root
        stack = [root]
        last_c = ''
        while o < n:
            c = text[o]
            if c == separator:
                if current.type != "sep":
                    current = current.append(Node("sep"))
            elif c == "<" and last_c != '\\':
                current = stack[-1].append(Node("tmpl"))
                stack.append(current)
            elif c == ">":
                if last_c == "<":
                    current.type = "sep"
                    current.cardinality = "?"
                elif last_c == "?":
                    current.value = current.value[:-1]
                    stack[-1].cardinality = "?"
                current = stack.pop()
            elif c == "|":
                current = stack[-1].append(Node("text"))
            elif current.type == "text":
                current.value = current.value + c
            else:
                current = stack[-1].append(Node("text", c))
            # End of iteration
            last_c = c
            o += 1
        return root

# EOF - vim: ts=4 sw=4 et
