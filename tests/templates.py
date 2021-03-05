from parsource import Template

# @group Parsing templates
EXPRESSIONS = {
	"<export?> class <NAME>":"(expr (tmpl (text export) (sep))? (text class (sep)) (tmpl (text NAME)))",
	"<var|const|let> <NAME>":"(expr (tmpl (text var) (text const) (text let) (sep)) (tmpl (text NAME)))",
	"var <NAME><>=<>":"(expr (text var (sep)) (tmpl (text NAME)) (sep)? (text =) (sep)?)",
}
for expr, template in EXPRESSIONS.items():
	t = Template.Parse(expr)
	assert repr(t) == template, f"Template is '{t}', expected: {template}"
	print (expr)
	print (" → ", t)
	print (" → ", t.toRegExp())

# @group Matching templates
MATCHING = {
	"<export?> class <NAME>":[
		"export class Foo",
		"class Foo",
	],
	"<var|const|let> <NAME>":[
		"var foo",
		"const foo",
		"let foo",
	],
	"var <NAME><>=<>":[
		"var foo=",
		"var foo =",
		"var foo = ",
	]
}
for template, matching in MATCHING.items():
	t = Template.Compile(template)
	for line in matching:
		assert t.match(line), f"Line not recognized by '{template}': {line}"


