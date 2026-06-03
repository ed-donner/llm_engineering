Semicolons¶
Like C, Go's formal grammar uses semicolons to terminate statements, but unlike in C, those semicolons do not appear in the source. Instead the lexer uses a simple rule to insert semicolons automatically as it scans, so the input text is mostly free of them.

The rule is this. If the last token before a newline is an identifier (which includes words like int and float64), a basic literal such as a number or string constant, or one of the tokens

break continue fallthrough return ++ -- ) }
the lexer always inserts a semicolon after the token. This could be summarized as, “if the newline comes after a token that could end a statement, insert a semicolon”.

A semicolon can also be omitted immediately before a closing brace, so a statement such as

    go func() { for { dst <- <-src } }()
needs no semicolons. Idiomatic Go programs have semicolons only in places such as for loop clauses, to separate the initializer, condition, and continuation elements. They are also necessary to separate multiple statements on a line, should you write code that way.

One consequence of the semicolon insertion rules is that you cannot put the opening brace of a control structure (if, for, switch, or select) on the next line. If you do, a semicolon will be inserted before the brace, which could cause unwanted effects. Write them like this

if i < f() {
    g()
}
not like this

if i < f()  // wrong!
{           // wrong!
    g()
}
Control structures¶
The control structures of Go are related to those of C but differ in important ways. There is no do or while loop, only a slightly generalized for; switch is more flexible; if and switch accept an optional initialization statement like that of for; break and continue statements take an optional label to identify what to break or continue; and there are new control structures including a type switch and a multiway communications multiplexer, select. The syntax is also slightly different: there are no parentheses and the bodies must always be brace-delimited.

If¶
In Go a simple if looks like this:

if x > 0 {
    return y
}
Mandatory braces encourage writing simple if statements on multiple lines. It's good style to do so anyway, especially when the body contains a control statement such as a return or break.

Since if and switch accept an initialization statement, it's common to see one used to set up a local variable.

if err := file.Chmod(0664); err != nil {
    log.Print(err)
    return err
}
In the Go libraries, you'll find that when an if statement doesn't flow into the next statement—that is, the body ends in break, continue, goto, or return—the unnecessary else is omitted.

f, err := os.Open(name)
if err != nil {
    return err
}
codeUsing(f)
This is an example of a common situation where code must guard against a sequence of error conditions. The code reads well if the successful flow of control runs down the page, eliminating error cases as they arise. Since error cases tend to end in return statements, the resulting code needs no else statements.

f, err := os.Open(name)
if err != nil {
    return err
}
d, err := f.Stat()
if err != nil {
    f.Close()
    return err
}
codeUsing(f, d)
Redeclaration and reassignment¶
An aside: The last example in the previous section demonstrates a detail of how the := short declaration form works. The declaration that calls os.Open reads,

f, err := os.Open(name)
This statement declares two variables, f and err. A few lines later, the call to f.Stat reads,

d, err := f.Stat()
which looks as if it declares d and err. Notice, though, that err appears in both statements. This duplication is legal: err is declared by the first statement, but only re-assigned in the second. This means that the call to f.Stat uses the existing err variable declared above, and just gives it a new value.

In a := declaration a variable v may appear even if it has already been declared, provided:

this declaration is in the same scope as the existing declaration of v (if v is already declared in an outer scope, the declaration will create a new variable §),
the corresponding value in the initialization is assignable to v, and
there is at least one other variable that is created by the declaration.
This unusual property is pure pragmatism, making it easy to use a single err value, for example, in a long if-else chain. You'll see it used often.

§ It's worth noting here that in Go the scope of function parameters and return values is the same as the function body, even though they appear lexically outside the braces that enclose the body.

For¶
The Go for loop is similar to—but not the same as—C's. It unifies for and while and there is no do-while. There are three forms, only one of which has semicolons.

// Like a C for
for init; condition; post { }

// Like a C while
for condition { }

// Like a C for(;;)
for { }
Short declarations make it easy to declare the index variable right in the loop.

sum := 0
for i := 0; i < 10; i++ {
    sum += i
}
If you're looping over an array, slice, string, or map, or reading from a channel, a range clause can manage the loop.

for key, value := range oldMap {
    newMap[key] = value
}
If you only need the first item in the range (the key or index), drop the second:

for key := range m {
    if key.expired() {
        delete(m, key)
    }
}
If you only need the second item in the range (the value), use the blank identifier, an underscore, to discard the first:

sum := 0
for _, value := range array {
    sum += value
}
The blank identifier has many uses, as described in a later section.

For strings, the range does more work for you, breaking out individual Unicode code points by parsing the UTF-8. Erroneous encodings consume one byte and produce the replacement rune U+FFFD. (The name (with associated builtin type) rune is Go terminology for a single Unicode code point. See the language specification for details.) The loop

for pos, char := range "日本\x80語" { // \x80 is an illegal UTF-8 encoding
    fmt.Printf("character %#U starts at byte position %d\n", char, pos)
}
prints

character U+65E5 '日' starts at byte position 0
character U+672C '本' starts at byte position 3
character U+FFFD '�' starts at byte position 6
character U+8A9E '語' starts at byte position 7
Finally, Go has no comma operator and ++ and -- are statements not expressions. Thus if you want to run multiple variables in a for you should use parallel assignment (although that precludes ++ and --).

// Reverse a
for i, j := 0, len(a)-1; i < j; i, j = i+1, j-1 {
    a[i], a[j] = a[j], a[i]
}
Switch¶
Go's switch is more general than C's. The expressions need not be constants or even integers, the cases are evaluated top to bottom until a match is found, and if the switch has no expression it switches on true. It's therefore possible—and idiomatic—to write an if-else-if-else chain as a switch.

func unhex(c byte) byte {
    switch {
    case '0' <= c && c <= '9':
        return c - '0'
    case 'a' <= c && c <= 'f':
        return c - 'a' + 10
    case 'A' <= c && c <= 'F':
        return c - 'A' + 10
    }
    return 0
}
There is no automatic fall through, but cases can be presented in comma-separated lists.

func shouldEscape(c byte) bool {
    switch c {
    case ' ', '?', '&', '=', '#', '+', '%':
        return true
    }
    return false
}
Although they are not nearly as common in Go as some other C-like languages, break statements can be used to terminate a switch early. Sometimes, though, it's necessary to break out of a surrounding loop, not the switch, and in Go that can be accomplished by putting a label on the loop and "breaking" to that label. This example shows both uses.

Loop:
    for n := 0; n < len(src); n += size {
        switch {
        case src[n] < sizeOne:
            if validateOnly {
                break
            }
            size = 1
            update(src[n])

        case src[n] < sizeTwo:
            if n+1 >= len(src) {
                err = errShortInput
                break Loop
            }
            if validateOnly {
                break
            }
            size = 2
            update(src[n] + src[n+1]<<shift)
        }
    }
Of course, the continue statement also accepts an optional label but it applies only to loops.

To close this section, here's a comparison routine for byte slices that uses two switch statements:

// Compare returns an integer comparing the two byte slices,
// lexicographically.
// The result will be 0 if a == b, -1 if a < b, and +1 if a > b
func Compare(a, b []byte) int {
    for i := 0; i < len(a) && i < len(b); i++ {
        switch {
        case a[i] > b[i]:
            return 1
        case a[i] < b[i]:
            return -1
        }
    }
    switch {
    case len(a) > len(b):
        return 1
    case len(a) < len(b):
        return -1
    }
    return 0
}
Type switch¶
A switch can also be used to discover the dynamic type of an interface variable. Such a type switch uses the syntax of a type assertion with the keyword type inside the parentheses. If the switch declares a variable in the expression, the variable will have the corresponding type in each clause. It's also idiomatic to reuse the name in such cases, in effect declaring a new variable with the same name but a different type in each case.

var t interface{}
t = functionOfSomeType()
switch t := t.(type) {
default:
    fmt.Printf("unexpected type %T\n", t)     // %T prints whatever type t has
case bool:
    fmt.Printf("boolean %t\n", t)             // t has type bool
case int:
    fmt.Printf("integer %d\n", t)             // t has type int
case *bool:
    fmt.Printf("pointer to boolean %t\n", *t) // t has type *bool
case *int:
    fmt.Printf("pointer to integer %d\n", *t) // t has type *int
}