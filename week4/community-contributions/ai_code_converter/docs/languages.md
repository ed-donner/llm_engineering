# Supported Languages

CodeXchange AI currently supports the following programming languages:

## Language Support Table

| Language   | Execution Method                        | File Extension |
|------------|----------------------------------------|----------------|
| Python     | Direct execution in restricted env      | .py            |
| JavaScript | Node.js                                | .js            |
| Java       | javac + java                           | .java          |
| C++        | g++ + executable                       | .cpp           |
| Julia      | julia                                  | .jl            |
| Go         | go run                                 | .go            |
| Ruby       | ruby                                   | .rb            |
| Swift      | swift                                  | .swift         |
| Rust       | rustc + executable                     | .rs            |
| C#         | csc (Mono)                             | .cs            |
| TypeScript | tsc + node                             | .ts            |
| R          | Rscript                                | .R             |
| Perl       | perl                                   | .pl            |
| Lua        | lua5.3                                 | .lua           |
| PHP        | php                                    | .php           |
| Kotlin     | kotlinc + kotlin                       | .kt            |
| SQL        | sqlite3                                | .sql           |

## Currently Implemented Languages

While the application has templates and instructions for all the languages listed above, the following languages are currently fully implemented with language detection and execution support:

- Python
- JavaScript
- Java
- C++
- Julia
- Go

## Language-Specific Notes

### Python
- Executed directly in a restricted environment
- Supports most standard libraries
- Execution timeout: 30 seconds

### JavaScript
- Executed using Node.js
- Supports ES6+ features
- No external npm packages are installed during execution

### Java
- Requires a class with a main method
- Class name must match filename
- Compiled with javac before execution

### C++
- Compiled with g++
- Standard C++17 support
- Execution timeout: 30 seconds

### Julia
- Executed with the julia interpreter
- Supports Julia 1.9+
- Limited package support during execution

### Go
- Executed with go run
- Supports Go 1.21+
- Standard library support only
