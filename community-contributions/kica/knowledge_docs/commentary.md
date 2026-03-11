Commentary¶
Go provides C-style /* */ block comments and C++-style // line comments. Line comments are the norm; block comments appear mostly as package comments, but are useful within an expression or to disable large swaths of code.

Comments that appear before top-level declarations, with no intervening newlines, are considered to document the declaration itself. These “doc comments” are the primary documentation for a given Go package or command. For more about doc comments, see “Go Doc Comments”.

Names¶
Names are as important in Go as in any other language. They even have semantic effect: the visibility of a name outside a package is determined by whether its first character is upper case. It's therefore worth spending a little time talking about naming conventions in Go programs.

Package names¶
When a package is imported, the package name becomes an accessor for the contents. After

import "bytes"
the importing package can talk about bytes.Buffer. It's helpful if everyone using the package can use the same name to refer to its contents, which implies that the package name should be good: short, concise, evocative. By convention, packages are given lower case, single-word names; there should be no need for underscores or mixedCaps. Err on the side of brevity, since everyone using your package will be typing that name. And don't worry about collisions a priori. The package name is only the default name for imports; it need not be unique across all source code, and in the rare case of a collision the importing package can choose a different name to use locally. In any case, confusion is rare because the file name in the import determines just which package is being used.

Another convention is that the package name is the base name of its source directory; the package in src/encoding/base64 is imported as "encoding/base64" but has name base64, not encoding_base64 and not encodingBase64.

The importer of a package will use the name to refer to its contents, so exported names in the package can use that fact to avoid repetition. (Don't use the import . notation, which can simplify tests that must run outside the package they are testing, but should otherwise be avoided.) For instance, the buffered reader type in the bufio package is called Reader, not BufReader, because users see it as bufio.Reader, which is a clear, concise name. Moreover, because imported entities are always addressed with their package name, bufio.Reader does not conflict with io.Reader. Similarly, the function to make new instances of ring.Ring—which is the definition of a constructor in Go—would normally be called NewRing, but since Ring is the only type exported by the package, and since the package is called ring, it's called just New, which clients of the package see as ring.New. Use the package structure to help you choose good names.

Another short example is once.Do; once.Do(setup) reads well and would not be improved by writing once.DoOrWaitUntilDone(setup). Long names don't automatically make things more readable. A helpful doc comment can often be more valuable than an extra long name.

Getters¶
Go doesn't provide automatic support for getters and setters. There's nothing wrong with providing getters and setters yourself, and it's often appropriate to do so, but it's neither idiomatic nor necessary to put Get into the getter's name. If you have a field called owner (lower case, unexported), the getter method should be called Owner (upper case, exported), not GetOwner. The use of upper-case names for export provides the hook to discriminate the field from the method. A setter function, if needed, will likely be called SetOwner. Both names read well in practice:

owner := obj.Owner()
if owner != user {
    obj.SetOwner(user)
}
Interface names¶
By convention, one-method interfaces are named by the method name plus an -er suffix or similar modification to construct an agent noun: Reader, Writer, Formatter, CloseNotifier etc.

There are a number of such names and it's productive to honor them and the function names they capture. Read, Write, Close, Flush, String and so on have canonical signatures and meanings. To avoid confusion, don't give your method one of those names unless it has the same signature and meaning. Conversely, if your type implements a method with the same meaning as a method on a well-known type, give it the same name and signature; call your string-converter method String not ToString.

MixedCaps¶
Finally, the convention in Go is to use MixedCaps or mixedCaps rather than underscores to write multiword names.