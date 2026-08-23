Introduction¶
Go is a new language. Although it borrows ideas from existing languages, it has unusual properties that make effective Go programs different in character from programs written in its relatives. A straightforward translation of a C++ or Java program into Go is unlikely to produce a satisfactory result—Java programs are written in Java, not Go. On the other hand, thinking about the problem from a Go perspective could produce a successful but quite different program. In other words, to write Go well, it's important to understand its properties and idioms. It's also important to know the established conventions for programming in Go, such as naming, formatting, program construction, and so on, so that programs you write will be easy for other Go programmers to understand.

This document gives tips for writing clear, idiomatic Go code. It augments the language specification, the Tour of Go, and How to Write Go Code, all of which you should read first.

Note added January, 2022: This document was written for Go's release in 2009, and has not been updated significantly since. Although it is a good guide to understand how to use the language itself, thanks to the stability of the language, it says little about the libraries and nothing about significant changes to the Go ecosystem since it was written, such as the build system, testing, modules, and polymorphism. There are no plans to update it, as so much has happened and a large and growing set of documents, blogs, and books do a fine job of describing modern Go usage. Effective Go continues to be useful, but the reader should understand it is far from a complete guide. See issue 28782 for context.

Examples¶
The Go package sources are intended to serve not only as the core library but also as examples of how to use the language. Moreover, many of the packages contain working, self-contained executable examples you can run directly from the go.dev web site, such as this one (if necessary, click on the word "Example" to open it up). If you have a question about how to approach a problem or how something might be implemented, the documentation, code and examples in the library can provide answers, ideas and background.

Formatting¶
Formatting issues are the most contentious but the least consequential. People can adapt to different formatting styles but it's better if they don't have to, and less time is devoted to the topic if everyone adheres to the same style. The problem is how to approach this Utopia without a long prescriptive style guide.

With Go we take an unusual approach and let the machine take care of most formatting issues. The gofmt program (also available as go fmt, which operates at the package level rather than source file level) reads a Go program and emits the source in a standard style of indentation and vertical alignment, retaining and if necessary reformatting comments. If you want to know how to handle some new layout situation, run gofmt; if the answer doesn't seem right, rearrange your program (or file a bug about gofmt), don't work around it.

As an example, there's no need to spend time lining up the comments on the fields of a structure. Gofmt will do that for you. Given the declaration

type T struct {
    name string // name of the object
    value int // its value
}
gofmt will line up the columns:

type T struct {
    name    string // name of the object
    value   int    // its value
}
All Go code in the standard packages has been formatted with gofmt.

Some formatting details remain. Very briefly:

Indentation
We use tabs for indentation and gofmt emits them by default. Use spaces only if you must.
Line length
Go has no line length limit. Don't worry about overflowing a punched card. If a line feels too long, wrap it and indent with an extra tab.
Parentheses
Go needs fewer parentheses than C and Java: control structures (if, for, switch) do not have parentheses in their syntax. Also, the operator precedence hierarchy is shorter and clearer, so
x<<8 + y<<16
means what the spacing implies, unlike in the other languages.