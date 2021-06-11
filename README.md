# Parsource

Parsource is a *cherry-picking parser* for source code, intended to be
used as a building block for tools such as documentation generators, tag generators,
high-level dataflow and other useful information.

Cherry-picking parsers are much looser than strict language parsers. As the name
suggests, they cherry pick the information they need, and gloss over things they don't
recognise. This makes it very easy to parse a language using a cherry-picking parser,
but the parse tree is going to be a bit rough.

A the moment, parsource supports the following.

-   JavaScript
-   Python
-   Go

But it is easy to add your own.

-  [NaturalDocs](https://www.naturaldocs.org/reference/scope/)
-  [Rosie Pattern Language](https://rosie-lang.org/)
-  [semgrep](https://github.com/returntocorp/semgrep).
-  Cherry picking parsing: skip over chunks of text and parse the contents… or not!
