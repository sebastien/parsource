import re
import fnmatch
from parsource.tree import Node
from typing import List, Tuple, Optional, Any

# --
# This is a simple tree-representation parser, so that the output of
# tree can be parsed back into a tree structure.

# NOTE: Merge this in tree
RE_NODE = re.compile(r"^(?P<indent>[├─└ ]*)(?P<name>[\w\-_]+)(?P<attrs>.*)?$")


def parse(text):
    """A simple TDoc parser"""
    stack: List[Tuple[int, Node]] = []
    indent = 0
    for line in text.split("\n"):
        match = RE_NODE.match(line)
        if not match:
            continue
        name = match.group("name")
        raw_attrs = [attr.strip().split("=")
                     for attr in (match.group("attrs") or "").split(" ") if attr.strip()]
        attrs = dict((_[0], eval(_[1])) for _ in raw_attrs)
        i = len(match.group("indent"))
        node = Node(name, **attrs)
        if not stack:
            stack.append((i, node))
        elif i == indent:
            stack[-2][1].append(node)
        elif i > indent:
            stack[-1][1].append(node)
            stack.append((i, node))
        else:
            while stack[-1][0] >= i:
                stack.pop()
            assert stack
            stack.append((indent, node))
        indent = i
    return stack[0][1]


# --
# ## Parser Combinators
#
# Now we introduce parser combinators to match subsets of a tree.

class Pattern:

    def __init__(self):
        self.slot: Optional[str] = None

    def match(self, node: Node) -> Any:
        raise NotImplementedError

    def __getitem__(self, key: str) -> 'Pattern':
        self.slot = key
        return self

    def __add__(self, other) -> 'Pattern':
        pat = other if isinstance(other, Pattern) else WithName(other)
        return SeqOf(self, pat)


class WithName(Pattern):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def match(self, node: Node) -> Optional[Tuple[Pattern, Node]]:
        return (self, node) if fnmatch.fnmatch(node.name, self.name) else None


class PatternOf(Pattern):

    def __init__(self, *patterns: Pattern):
        super().__init__()
        self.of: List[Pattern] = [_ for _ in patterns]

    def match(self, node: Node) -> Any:
        raise NotImplementedError


class SeqOf(PatternOf):

    def match(self, node: Node) -> Optional[Tuple[Pattern, List[Node]]]:
        res: List[Node] = []
        cur: Optional[Node] = node
        for pat in self.of:
            if not cur:
                return None
            elif not pat.match(cur):
                return None
            res.append(cur)
            cur = cur.nextSibling
        return (self, res)

    def __add__(self, other) -> 'Pattern':
        pat = other if isinstance(other, Pattern) else WithName(other)
        self.of.append(pat)
        return self


class AnyOf(Pattern):

    def __init__(self, *patterns: Pattern):
        super().__init__()
        self.of: List[Pattern] = [_ for _ in patterns]

    def match(self, node: Node) -> Optional[Tuple[Pattern, Node]]:
        for pat in self.of:
            if (res := pat.match(node)):
                return (self, res)
        return None

# --
# And a declarative API to take care of it.


def named(name):
    return WithName(name)


def find(pattern: Pattern, tree: Node):
    for node in tree.walk():
        if match := pattern.match(node):
            print("MATCH", match, node)


TREE = parse("""
root
├─ keyword value='let'
├─ text value='a'
├─ op-inf value=''
└─ text value='10'
""")
Expr = named("text")["left"] + named("op-inf")["op"] + named("text")["right"]

print(find(Expr, TREE))
