import re
from typing import Iterable, Tuple, List, Dict, Any, Iterable, Optional
from parsource.parser import ParseEvent, iterMatches
from parsource.tree import Node, TreeTransform

# -----------------------------------------------------------------------------
#
# TRANSFORM
#
# -----------------------------------------------------------------------------


class Transform:
    """An abstract transformation of the input stream."""

    def __init__(self):
        super().__init__()
        self.value = None
        self.reset()

    def reset(self):
        pass

    def preProcess(self):
        pass

    def postProcess(self):
        pass

    def feed(self, event: ParseEvent) -> Optional[Exception]:
        return None

    def process(self, stream: Iterable[ParseEvent]) -> Iterable[Exception]:
        self.preProcess()
        for event in stream:
            res: Optional[Exception] = self.feed(event)
            if res:
                yield res
        self.postProcess()

# -----------------------------------------------------------------------------
#
# TREE EXTRACTOR
#
# -----------------------------------------------------------------------------


class TreeExtractor(Transform):
    """Extracts a tree from the parse stream."""

    def __init__(self, offsets=True):
        super().__init__()
        self.withOffsets = offsets

    def reset(self):
        self.value = Node("root")
        self.stack: List[Tuple[Node, str]] = [(self.value, "")]
        self.normalizer = NormalizeTree()

    def postProcess(self):
        # self.normalizer.run(self.value)
        return self.value

    @property
    def current(self) -> Node:
        return self.stack[-1][0]

    @property
    def currentEvent(self) -> str:
        return self.stack[-1][1]

    def push(self, node: Node, eventType: str):
        self.stack.append((node, eventType))
        return node

    def pop(self):
        old = self.stack.pop()[0]
        if not self.stack:
            raise Exception(f"More pops than pushes at {self.stack}")
        else:
            cur = self.stack[-1][0]
            assert old in cur, f"Expected popped value '{old}' to be in the current value: {cur}"
            return cur

    def append(self, node: Node):
        self.current.append(node)
        return node

    def feed(self, event: ParseEvent) -> Optional[Exception]:
        if event.type == ParseEvent.COMMENT:
            self.push(self.append(self.node(event, "comment")),
                      ParseEvent.LINE_END)
        elif event.type == ParseEvent.BLOCK_START:
            self.push(self.append(
                self.node(event, "block", type=event.value)), event.type)
        elif event.type == ParseEvent.LINE_END:
            if self.currentEvent == ParseEvent.LINE_END:
                self.pop()
        elif event.type == ParseEvent.STATEMENT_END:
            # A statement will integrate the any previous sibling of the
            # current node that is not a statement.
            prev_statement = next((i for i, n in enumerate(
                reversed(self.current.children)) if n.name == "statement"), 0)
            node = self.node(event, "statement")
            for child in self.current.children[prev_statement:]:
                node.add(child.detach())
            self.append(node)
        elif event.type == ParseEvent.BLOCK_END:
            self.pop()
        elif event.type == ParseEvent.QUOTE:
            self.append(self.node(event, "quote", value=event.text))
        elif event.type == ParseEvent.TEXT:
            self.append(self.node(event, "text", value=event.text))
        elif event.type == ParseEvent.KEYWORD:
            self.append(self.node(event, "keyword", value=event.text))
        elif event.type == ParseEvent.OPERATOR_INFIX:
            self.append(self.node(event, "op-inf", value=event.text))
        elif event.type == ParseEvent.OPERATOR_SUFFIX:
            self.append(self.node(event, "op-suf", value=event.text))
        elif event.type == ParseEvent.OPERATOR_PREFIX:
            self.append(self.node(event, "op-pre", value=event.text))
        else:
            raise ValueError(f"Unsupported event: {event}")

    def node(self, event: ParseEvent, name: str, **attributes: Dict[str, str]):
        """Helper to create nodes and store the parsing offsets."""
        node = Node(name, **attributes)
        if self.withOffsets:
            node.setAttribute("start", event.start)
            node.setAttribute("end", event.end)
        return node

# -----------------------------------------------------------------------------
#
# TREE NORMALIZATION
#
# -----------------------------------------------------------------------------
# NOTE: We can see here how the transformation is really not ideal and should
# probably be captured differently. On the one hand it's convenient to mutate
# the tree in-place, on the other hand it makes reasoning about it quite
# hard.


class CommentProcessor(TreeTransform):

    PATTERNS = {
        (re.compile("@(?P<value>[a-z][a-z0-9]+)")): "directive",
        (re.compile(r"--\s+|―\s*")): "separator",
    }

    def on_block(self, node: Node):
        if node["type"] == "(":
            args = [Node("text", value=_.strip()) for _ in "".join(
                node.walk(processor=lambda _:_["value"] if "value" in _ else "")).split(",")]
            node.setChildren(args)
            node.name = "args"
            if node.previousSibling and node.previousSibling.name == "directive":
                node.previousSibling.append(node.detach())

    def on_text(self, node: Node):
        text = node["value"]
        res = []
        assert node.count == 0, f"Text node has children, but should not have: {node}"
        for start, end, pattern, match in iterMatches(text, list(self.PATTERNS.keys())):
            if pattern:
                child = Node(self.PATTERNS[pattern])
                try:
                    value = match.group("value")
                except IndexError as e:
                    value = None
            else:
                child = Node("text")
                value = text[start:end]
            if value:
                child.setAttribute("value", value)
            res.append(child.updateAttributes(dict(
                start=node["start"] + start,
                end=node["start"] + end,
            )))
        node.name = "parsed-comment"
        node.removeAttribute("value")
        node.replaceWith(res)


class NormalizeTree(TreeTransform):
    """Normalizes the tree."""

    Comments = CommentProcessor()

    def on_text(self, node):
        """We move text back into statements."""
        if node.parent.name != "statement":
            node.wrap(Node("statement"))

    def on_statement(self, node):
        """We absorb statement text siblings"""
        while node.nextSibling and node.nextSibling.name == "text":
            node.append(node.nextSibling.detach())
        if not node.count:
            node.detach()

    def on_text(self, node):
        pass

    def on_comment(self, node: Node):
        self.Comments.process(node)
        # This essentially merges the comment back to its parent
        # ├─ comment start=0 end=2
        # │  ├─ directive value='function' start=3 end=12
        # │  ├─ text value=' Some function' start=12 end=26
        # │  └─ comment start=27 end=29
        # │     └─ text value='with a documentation there' start=30 end=56
        # becomes
        # ├─ comment start=0 end=2
        # │  ├─ directive value='function' start=3 end=12
        # │  ├─ text value=' Some function' start=12 end=26
        # │  └─ text value='with a documentation there' start=30 end=56
        if node.previousSibling and node.firstChild and node.firstChild.name != "directive":
            for child in node.children:
                node.previousSibling.append(child.detach())
            node.detach()

    # FIXME: This does not work because that does not recurse. We should
    # have the
    # def on_block( self, node ):
    # 	if node.count == 1 and node.firstChild.name == "statement":
    # 		node.absorb(node.firstChild)

# EOF
