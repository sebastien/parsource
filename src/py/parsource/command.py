from parsource import Parser
from parsource.lang.js import JavaScript
from parsource.transform import TreeExtractor
import sys


def run(args=sys.argv[1:]):
    for a in args:
        with open(a, "rt") as f:
            extractor = TreeExtractor()
            for error in extractor.process(JavaScript.parse(f.read())):
                print("ERROR", error)
            print(extractor.value.toTDoc())

# EOF
