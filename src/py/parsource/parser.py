from typing import Iterable, Tuple, Any, Iterable, Optional, Dict, List, Pattern, Match, Union, NamedTuple


# --
# # Language definition
#
# Language definitions provide the basic information to extract the overall structure
# of most common programming languages. Languages have *statements* and *comments*. Statements
# are organised in *blocks*. Text strings are defined by start and end *quotes*.
#
# Each `Language` class defines:
#
# - `Language.ESCAPE`
# - `Language.TRIM`
# - `Language.STATEMENT_END`
# - `Language.LINE_END`
# - `Language.COMMENTS`
# - `Language.BLOCKS`
# - `Language.QUOTES`


class BlockLanguage:
    """Defines what we can find in a language."""
    ESCAPE: str = "\\"
    TRIM: str = " \t\n"
    STATEMENT_END: List[str] = [";", ":"]
    LINE_END: List[str] = ["\n"]
    COMMENTS: List[str] = ["//", "#"]
    BLOCKS: List[Tuple[str, str]] = [
        ('{', '}'),
        ('[', ']'),
        ('(', ')'),
        ('/*', '*/'),
    ]
    QUOTES: List[str] = ['"', "'", '"""']

    def __init__(self):
        # For blocks
        self.escape = self.ESCAPE
        self.trim = self.TRIM
        self.statementEnd = self.STATEMENT_END
        self.lineEnd = self.LINE_END
        self.comments = self.COMMENTS
        self.blocks = self.BLOCKS
        self.quotes = self.QUOTES
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


class ExpressionLanguage:

    ESCAPE: str = "\\"
    TRIM: str = " \t\n"
    SEPARATORS: List[str] = [" ", "\t"]
    KEYWORDS: List[str] = []
    OPERATOR_INFIX: List[str] = []
    OPERATOR_PREFIX: List[str] = []
    OPERATOR_SUFFIX: List[str] = []

    def __init__(self):
        # For expressions
        self.escape = self.ESCAPE
        self.trim = self.TRIM
        self.separators = self.SEPARATORS
        self.keywords = self.KEYWORDS
        self.opInfix = self.OPERATOR_INFIX
        self.opPrefix = self.OPERATOR_PREFIX
        self.opSuffix = self.OPERATOR_SUFFIX
        self.operators = self.opInfix + self.opPrefix + self.opSuffix
        self.delimiters = self.separators + self.keywords + \
            self.opInfix + self.opPrefix + self.opSuffix


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
    KEYWORD = ":keyword"
    OPERATOR_INFIX = ":op-infix"
    OPERATOR_SUFFIX = ":op-suffix"
    OPERATOR_PREFIX = ":op-prefix"
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
        assert self._text is not None
        return self._text

    def __repr__(self):
        return f"(Event {self.type} {repr(self.text)}{' ' + repr(self.value) if self.value else ''})"

# -----------------------------------------------------------------------------
#
# PARSER
#
# -----------------------------------------------------------------------------


class BlockParser:
    """Parses source files using a `BlockLanguage` configuration, extracting
    tags from source comments and extracting some of the structure."""

    def __init__(self, language: BlockLanguage):
        self.lang = language

    def parse(self, text: str) -> Iterable[ParseEvent]:
        """Parses the given text, yielding events."""
        quote_start: int = -1
        quote_type: Optional[str] = None
        for start, end, delim in iterDelimiters(text, self.lang.delimiters, self.lang.escape):
            # Quotes need to swallow any other delimiter, so that's what we do
            # here.
            if quote_type:
                if delim != quote_type:
                    # If we're in a quote, we'll swallow any event up until
                    # we encounter the end quote.
                    pass
                else:
                    # We'll only yield events that are outside of quotes.
                    quote_type = None
                    yield ParseEvent(ParseEvent.QUOTE, text, quote_start, end, delim)
            else:
                delim_start = end - len(delim)
                if start < delim_start:
                    text_start, text_end = trim(
                        text, self.lang.trim, start, delim_start)
                    if text_start < text_end:
                        yield ParseEvent(ParseEvent.TEXT, text, text_start, text_end)
                # The language object will define what is an event type
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


class ExpressionParser:
    """Parses source expressions using an `ExpressionLanguage` configuration."""

    def __init__(self, language: ExpressionLanguage):
        self.lang = language

    def parse(self, text: str) -> Iterable[ParseEvent]:
        """Parses the given text, yielding events."""
        lang = self.lang
        offset = 0
        for start, end, delim in iterDelimiters(text, lang.delimiters, lang.escape):
            if offset < start:
                yield ParseEvent(ParseEvent.TEXT, text, offset, start)
            if delim is None:
                print("REST", text[offset])
            elif delim in lang.keywords:
                yield ParseEvent(ParseEvent.KEYWORD, delim, start, end, delim)
            elif delim in lang.opInfix:
                yield ParseEvent(ParseEvent.OPERATOR_INFIX, delim, start, end, delim)
            elif delim in lang.opPrefix:
                yield ParseEvent(ParseEvent.OPERATOR_PREFIX, delim, start, end, delim)
            elif delim in lang.opSuffix:
                yield ParseEvent(ParseEvent.OPERATOR_SUFFIX, delim, start, end, delim)
            elif delim in lang.separators:
                pass
            else:
                raise RuntimeError("Unsupported", delim)
            offset = end
        if offset < len(text):
            yield ParseEvent(ParseEvent.TEXT, text, offset, len(text))

# --
# # Utility functions


def trim(text: str, trim: str, start: int, end: int) -> Tuple[int, int]:
    """Returns the `(start,end)` offsets in the given text after skipping characters to
    be trimmed from the given `start` and `end` positions."""
    while start < end and text[start] in trim:
        start += 1
    while start < end and text[end - 1] in trim:
        end -= 1
    return (start, end)


DelimiterMatch = NamedTuple(
    'DelimiterMatch', [("start", int), ("end", int), ("delim", Optional[str])])


def iterDelimiters(text: str, delimiters: List[str], escape: str, lookahead: int = 256) -> Iterable[DelimiterMatch]:
    """Iterates triples `(start,end,delim)` couples for every delimiter that
    was found up to `lookahead` distance (in characters), choosing the closest
    one each time. This is essentially like splitting a string based on a list
    of delimiters, taking into account an `escape` character."""
    # We start at 0, up until the end of the text
    offset = 0
    end = len(text)
    # While we haven't reached the end
    while offset < end:
        i = end
        d = None
        # We iterate through the delimiters
        for delim in delimiters:
            # Look for the closest index of the delimiter, up to lookahead or
            # just before the next delimiter with a 16 chars lookahead
            j = text.find(delim, offset, min(i + 16, offset + lookahead))
            # Now we've found a closest delimiter, so we use that one
            if j >= 0 and j < i and (j == 0 or text[j - 1] != escape):
                i = j
                d = delim
        # We have a delimiter, so we can now  yield the result
        if d is not None:
            n = len(d)
            yield DelimiterMatch(i, i + n, d)
            offset = i + n
        # We don't have a delimiter, so we need to skip lookahead.
        # We don't yield any result, as we haven't found a delimiter.
        else:
            i = min(offset+lookahead, end)
            offset = i
    if offset < end:
        yield DelimiterMatch(offset, end, None)


# FIMXE: This is not used ATM
def iterMatches(text: str, delimiters: List[Pattern]) -> Iterable[Tuple[int, int, Optional[Pattern], Union[Match, str]]]:
    """Iterates on all the matches from the given regex pattern, using a strategy
    where the largest closest match wins. This is the core of the cherry-picking
    strategy."""
    matches: List[Tuple[Pattern, Match]] = []
    # We get all matching delimiter, it's not ideal but we do need to iterate
    # on all the patterns for all the positions.
    for pattern in delimiters:
        matches += [(pattern, _) for _ in pattern.finditer(text)]
    # We now sort the matches by start and length. The longest match is the one
    # that will win.
    n = len(text)
    matches = sorted(matches, key=lambda _: _[
        1].start() * n + (_[1].end() - _[1].start()))
    # We start with an offset of -1 (start of text)
    offset = 0
    # Now we iterate on each match
    for pattern, match in matches:
        # The match has (i,j) start and end offsets in the text
        i, j = match.start(), match.end()
        # We yield a text match for the inbetween text
        if i != offset:
            yield 0, i, None, text[offset:i]
        # We yield the pattern match
        yield i, j, pattern, match
        offset = j
    # We yield a text match
    if offset < n:
        yield offset, n, None, text[offset:]


# EOF
