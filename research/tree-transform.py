import re
import fnmatch
from parsource.tree import Node
from typing import List, Tuple, Optional, Any, Union, NamedTuple, Dict

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

Match = NamedTuple("Match", [("pattern", 'Pattern'),
                             ("value", Union[Node, List['Match']]), ("slot", Optional[str])])


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

    def match(self, node: Node) -> Optional[Match]:
        return Match(self, self.slot, node) if fnmatch.fnmatch(node.name, self.name) else None


class PatternOf(Pattern):

    def __init__(self, *patterns: Pattern):
        super().__init__()
        self.of: List[Pattern] = [_ for _ in patterns]

    def match(self, node: Node) -> Any:
        raise NotImplementedError


class SeqOf(PatternOf):

    def match(self, node: Node) -> Optional[Match]:
        res: List[Node] = []
        cur: Optional[Node] = node
        for pat in self.of:
            if not cur:
                return None
            elif not (match := pat.match(cur)):
                return None
            res.append(match)
            cur = cur.nextSibling
        return Match(self, res, self.slot)

    def __add__(self, other) -> 'Pattern':
        pat = other if isinstance(other, Pattern) else WithName(other)
        self.of.append(pat)
        return self


class AnyOf(Pattern):

    def __init__(self, *patterns: Pattern):
        super().__init__()
        self.of: List[Pattern] = [_ for _ in patterns]

    def match(self, node: Node) -> Optional[Match]:
        for pat in self.of:
            if (res := pat.match(node)):
                return Match(self, res, self.slot)
        return None

# --
# And a declarative API to take care of it.


def named(name):
    return WithName(name)


def find(pattern: Pattern, tree: Node):
    for node in tree.walk():
        if match := pattern.match(node):
            # TODO: Should be a yield
            return match


TSlots = Dict[str, Union[Node, List[Node]]]


def slots(match: Match) -> TSlots:
    slots: TSlots = {}

    def helper(value: Union[Match, Node, List[Union[Match, Node]]], slots: TSlots):
        if not value:
            return value
        if isinstance(value, Node):
            print("NODE", value)
            res = value
        elif isinstance(value, List):
            print("LIST", value)
            res = [helper(_, slots) for _ in value]
        else:
            print("MATCH", value)
            # We have a match
            match = value
            res = helper(match.value, slots)
            if (name := match.slot) and name not in slots:
                slots[name] = res
        slots["_"] = res
        return res
    helper(match, slots)
    return slots


TREE = parse("""
root
├─ keyword value='let'
├─ text value='a'
├─ op-inf value=''
└─ text value='10'
""")
Expr = named("text")["left"] + named("op-inf")["op"] + named("text")["right"]

match = find(Expr, TREE)
print(match)
print(slots(match))
