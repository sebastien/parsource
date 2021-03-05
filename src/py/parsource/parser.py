from typing import Iterable, Tuple, Any, Iterable, Optional, Dict, List, Pattern, Match, Union

# -----------------------------------------------------------------------------
#
# LANGUAGE
#
# -----------------------------------------------------------------------------


class Language:
    """Defines what we can find in a language."""

    def __init__(self):
        self.escape = "\\"
        self.trim = " \t\n"
        self.statementEnd = [";", ":"]
        self.lineEnd = ["\n"]
        self.comments = ["//", "#"]
        self.blocks = [
            ('{', '}'),
            ('[', ']'),
            ('(', ')'),
            ('/*', '*/'),
        ]
        self.quotes = ['"', "'", '"""']
        self.blockStart = [_[0] for _ in self.blocks]
        self.blockEnd = [_[1] for _ in self.blocks]
        self.blockMatch = dict(
            [(k, v) for k, v in self.blocks] + [(v, k) for k, v in self.blocks])
        self.delimiters = [self.escape] + self.comments + self.blockStart + \
            self.blockEnd + self.quotes + self.lineEnd + self.statementEnd
        # Now we pre-calculate the events map, for speed
        self.events: Dict[str, str] = {}
        for delims, event_type in (
                (self.comments,     ParseEvent.COMMENT),
                (self.lineEnd,      ParseEvent.LINE_END),
                (self.statementEnd, ParseEvent.STATEMENT_END),
                (self.blockStart,   ParseEvent.BLOCK_START),
                (self.blockEnd,     ParseEvent.BLOCK_END),
                (self.quotes,       ParseEvent.QUOTE),
        ):
            for delim in delims:
                self.events[delim] = event_type

# -----------------------------------------------------------------------------
#
# PARSE EVENT
#
# -----------------------------------------------------------------------------


class ParseEvent:
    """Abstracts away events emitted by the parser."""

    TEXT = ":text"
    COMMENT = ":comment"
    QUOTE = ":quote"
    LINE_END = ":line-end"
    STATEMENT_END = ":statement-end"
    BLOCK_START = ":block-start"
    BLOCK_END = ":block-end"

    def __init__(self, type: str, source: str, start: int, end: int, value: Any = None):
        self.type = type
        self.source = source
        self.start = start
        self.end = end
        self.value = value
        self._text: Optional[str] = None

    @property
    def text(self) -> str:
        if self._text == None:
            self._text = self.source[self.start:self.end]
        return self._text

    def __repr__(self):
        return f"(Event {self.type} {repr(self.text)}{' ' + repr(self.value) if self.value else ''})"

# -----------------------------------------------------------------------------
#
# PARSER
#
# -----------------------------------------------------------------------------


class Parser:
    """Parses source files using a `Language` configuration, extracting
    tags from source comments and extracting some of the structure."""

    def __init__(self):
        self.lang = Language()

    def parse(self, text: str) -> Iterable[ParseEvent]:
        """Parses the given text, yielding events."""
        quote_start: int = -1
        quote_type: Optional[str] = None
        for start, end, delim in iterDelimiters(text, self.lang.delimiters, self.lang.escape):
            # Quotes need to swallow any other delimiter, so that's what we do
            # here.
            if quote_type:
                # We'll only yield events that are outside of quotes.
                if delim == quote_type:
                    quote_type = None
                    yield ParseEvent(ParseEvent.QUOTE, text, quote_start, end, delim)
                else:
                    pass
            else:
                delim_start = end - len(delim)
                if start < delim_start:
                    text_start, text_end = trim(
                        text, self.lang.trim, start, delim_start)
                    if text_start < text_end:
                        yield ParseEvent(ParseEvent.TEXT, text, text_start, text_end)
                event_type = self.lang.events.get(delim)
                # If we have a quote, it will start swallowing the other
                # delimiters.
                if event_type == ParseEvent.QUOTE:
                    quote_type = delim
                    quote_start = delim_start
                    # We yield the text before the quote
                elif event_type:
                    yield ParseEvent(event_type, text, delim_start, end, delim)
                else:
                    raise ValueError(f"Unknown delimiter {repr(delim)}")

# -----------------------------------------------------------------------------
#
# FUNCTION
#
# -----------------------------------------------------------------------------


def trim(text: str, trim: str, start: int, end: int) -> Tuple[int, int]:
    """Returns the `(start,end)` couple after skipping characters to
    be trimmed (`self.lang.trim`)."""
    while start < end and text[start] in trim:
        start += 1
    while start < end and text[end - 1] in trim:
        end -= 1
    return (start, end)


def iterMatches(text: str, delimiters: List[Pattern]) -> Iterable[Tuple[int, int, Optional[Pattern], Union[Match, str]]]:
    """Iterates on all the matches from the given pattern, using a strategy
    where the largest closest match wins."""
    matches: List[Tuple[Pattern, Match]] = []
    # We get all the matches, it's not ideal but we do need to iterate
    # on all the patterns for all the positions.
    for pattern in delimiters:
        matches += [(pattern, _) for _ in pattern.finditer(text)]
    # We sort the matches by start and length (largest wins)
    n = len(text)
    matches = sorted(matches, key=lambda _: _[
                     1].start() * n + (_[1].end() - _[1].start()))
    offset = 0
    for p, m in matches:
        i, j = m.start(), m.end()
        if offset != i:
            yield offset, i, None, text[offset:i]
        yield i, j, p, m
        offset = j
    if offset < n:
        yield offset, n, None, text[offset:]


def iterDelimiters(text: str, delimiters: List[str], escape: str, lookahead: int = 320) -> Iterable[Tuple[int, int, str]]:
    """Iterates triples `(start,end,delim)` couples for every delimiter that
    was found up to `lookahead` distance."""
    offset = 0
    end = len(text)
    while offset < end:
        i = end
        d = None
        for _ in delimiters:
            j = text.find(_, offset, offset + lookahead)
            if j >= offset and j <= end and j < i and (j == 0 or text[j - 1] != escape):
                i = j
                d = _
        n = len(d)
        yield offset, i + n, d
        offset = i + n
    if offset < end:
        yield offset, end, None

# EOF
