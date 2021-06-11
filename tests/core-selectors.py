from parsource.parser import Language, Parser
from parsource.transform import TreeExtractor


class SelectorLang(Language):
    ESCAPE = "\\"
    TRIM = " \t\n"
    STATEMENT_END = [","]
    LINE_END = ["\n"]
    BLOCKS = [
        ('[', ']'),
        ('{', '}'),
    ]
    QUOTES = ['"', "'"]


parser = Parser(SelectorLang())
extractor = TreeExtractor(offsets=False)
text = "*[type=QM],{type,time}"
for error in extractor.process(parser.parse(text)):
    print("ERROR", error)
print(extractor.value.toXML())
