from parsource.lang.js import JavaScriptExpression
from parsource.parser import ExpressionParser
from parsource.transform import TreeExtractor


def parse(text: str):
    extractor = TreeExtractor(offsets=False)
    parser = ExpressionParser(JavaScriptExpression())
    errors = [_ for _ in extractor.process(parser.parse(text))]
    return extractor.value


#            0123456789
print(parse("let a = 10").toTDoc())
# print(parse("const a = 10").toTDoc())
