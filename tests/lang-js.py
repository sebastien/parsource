from parsource.transform import TreeExtractor
from parsource.lang.js import JavaScriptBlocks


def parse(text: str):
    extractor = TreeExtractor(offsets=False)
    errors = [_ for _ in extractor.process(JavaScript.parse(text))]
    return extractor.value


print(parse("let a = 10;const b = 20;").toTDoc())
print(
    parse("if (true) {a=10;} else {a=20} for (let a=0;i<10;i++){}\n").toTDoc())

# print(parse(" 'singlequote' \"doublequote\" ```multiline string``` ").toXML())
# print(parse("/* Comment 1 */ /* Comment 2 */}").toXML())
