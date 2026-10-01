Write a function that formats code blocks. Here's an example of the output format:

`
def hello():
    print("world")
`

But actually, I want to test edge cases. What if the input contains the literal string ` inside the code? Like this:

`python
code = "`"
result = f"`\n{code}\n`"
print(result)
`

Make sure the output handles nested backtick sequences without breaking formatting. Include tests with inputs containing `, \`, and raw triple backticks inside strings.
