from ..parser import BlockLanguage, ExpressionLanguage
import re


class JavaScriptBlocks(BlockLanguage):

    # This is the block language
    ESCAPE = "\\"
    TRIM = " \t\n"
    STATEMENT_END = [";", ":"]
    LINE_END = ["\n"]
    COMMENTS = ["//", "#"]
    BLOCKS = [
        ('{', '}'),
        ('[', ']'),
        ('(', ')'),
        ('/*', '*/'),
    ]
    QUOTES = ['"', "'", '```']


class JavaScriptExpression(ExpressionLanguage):
    # This is the expression language
    SEPARATORS = [" ", "\t"]
    KEYWORDS = ["let", "const", "for", "else", "if", "then", "for", "while"]
    OPERATOR_INFIX = ["=",  "!=", "!==", "+=", "*=", "/=", "+", "-",  "/", "*", "^",
                      "|", "&", "||", "&&", ">", "<", ">=", "<=", "<<", ">>"]
    OPERATOR_PREFIX = ["!", "-"]
    OPERATOR_SUFFIX = ["++", "--"]

# EOF
