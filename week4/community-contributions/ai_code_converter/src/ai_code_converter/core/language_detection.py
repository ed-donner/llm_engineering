"""Module for detecting programming languages in code snippets."""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Class for detecting programming languages in code snippets."""
    
    @staticmethod
    def detect_python(code: str) -> bool:
        """Detect if code is Python."""
        patterns = [
            r'def\s+\w+\s*\([^)]*\)\s*:',  # Function definition
            r'import\s+[\w\s,]+',           # Import statements
            r'from\s+[\w.]+\s+import',      # From import statements
            r'print\s*\([^)]*\)',           # Print statements
            r':\s*$'                        # Line ending with colon
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    @staticmethod
    def detect_javascript(code: str) -> bool:
        """Detect if code is JavaScript."""
        patterns = [
            r'function\s+\w+\s*\([^)]*\)',  # Function declaration
            r'const\s+\w+\s*=',             # Const declaration
            r'let\s+\w+\s*=',               # Let declaration
            r'var\s+\w+\s*=',               # Var declaration
            r'console\.(log|error|warn)'    # Console methods
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    @staticmethod
    def detect_java(code: str) -> bool:
        """Detect if code is Java."""
        patterns = [
            r'public\s+class\s+\w+',        # Class declaration
            r'public\s+static\s+void\s+main', # Main method
            r'System\.(out|err)\.',         # System output
            r'private|protected|public',     # Access modifiers
            r'import\s+java\.'              # Java imports
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    @staticmethod
    def detect_cpp(code: str) -> bool:
        """Detect if code is C++."""
        patterns = [
            r'#include\s*<[^>]+>',          # Include statements
            r'std::\w+',                    # STD namespace usage
            r'cout\s*<<',                   # Console output
            r'cin\s*>>',                    # Console input
            r'int\s+main\s*\('              # Main function
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    @staticmethod
    def detect_julia(code: str) -> bool:
        """Detect if code is Julia."""
        patterns = [
            r'function\s+\w+\s*\([^)]*\)\s*end', # Function with end
            r'println\(',                   # Print function
            r'using\s+\w+',                # Using statement
            r'module\s+\w+',               # Module declaration
            r'struct\s+\w+'                # Struct declaration
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    @staticmethod
    def detect_go(code: str) -> bool:
        """Detect if code is Go."""
        patterns = [
            r'package\s+\w+',              # Package declaration
            r'func\s+\w+\s*\(',            # Function declaration
            r'import\s*\(',                # Import block
            r'fmt\.',                      # fmt package usage
            r'type\s+\w+\s+struct'         # Struct declaration
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    @staticmethod
    def detect_ruby(code: str) -> bool:
        """Detect if code is Ruby."""
        patterns = [
            r'def\s+\w+\s*(?:\([^)]*\))?\s*$', # Method definition without end
            r'class\s+\w+(?:\s*<\s*\w+)?\s*$', # Class definition without end
            r'require\s+["\']\w+["\']',    # Require statement
            r'\b(?:puts|print)\s',          # Output methods
            r'\bdo\s*\|[^|]*\|',            # Block with parameters
            r'\bend\b',                    # End keyword
            r':[a-zA-Z_]\w*\s*=>',          # Symbol hash syntax
            r'[a-zA-Z_]\w*:\s*[^,\s]'      # New hash syntax
        ]
        return any(re.search(pattern, code) for pattern in patterns)
        
    @staticmethod
    def detect_swift(code: str) -> bool:
        """Detect if code is Swift."""
        patterns = [
            r'import\s+(?:Foundation|UIKit|SwiftUI)',  # Common Swift imports
            r'(?:var|let)\s+\w+\s*:\s*\w+',         # Variable declaration with type
            r'func\s+\w+\s*\([^)]*\)\s*(?:->\s*\w+)?\s*\{',  # Function declaration
            r'class\s+\w+(?:\s*:\s*\w+)?\s*\{',    # Class declaration
            r'struct\s+\w+\s*\{',                    # Struct declaration
            r'@IBOutlet|@IBAction',                    # iOS annotations
            r'guard\s+let',                           # Guard statement
            r'if\s+let|if\s+var',                     # Optional binding
            r'override\s+func',                       # Method override
            r'\bimport\s+Swift\b',                   # Swift import 
            r'\?\?',                                 # Nil coalescing operator
            r'extension\s+\w+',                      # Extensions
            r'protocol\s+\w+',                       # Protocols
            r'enum\s+\w+\s*(?::\s*\w+)?\s*\{',      # Enums
            r'case\s+\w+(?:\(.*?\))?',               # Enum cases
            r'typealias\s+\w+',                      # Type aliases
            r'init\s*\(',                            # Initializer
            r'deinit\s*\{',                          # Deinitializer
            r'\$\d+',                                # String interpolation
            r'\bOptional<',                          # Optional type
            r'\bas\?',                               # Type casting
            r'\bas!',                                # Forced type casting
            r'convenience\s+init',                    # Convenience initializer
            r'required\s+init',                      # Required initializer
            r'\bUInt\d*\b',                          # Swift integer types
            r'\bInt\d*\b',                           # Swift integer types
            r'\barray<',                             # Swift arrays
            r'\bdictionary<',                        # Swift dictionaries
            r'@escaping',                            # Escaping closures
            r'\bweak\s+var',                         # Weak references
            r'\bunowned\b'                            # Unowned references
        ]
        return any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns)

    @staticmethod
    def detect_rust(code: str) -> bool:
        """Detect if code is Rust."""
        patterns = [
            r'fn\s+\w+\s*\([^)]*\)\s*(?:->\s*[^{]+)?\s*\{',  # Function declaration
            r'let\s+mut\s+\w+',                # Mutable variable declaration
            r'struct\s+\w+\s*\{[^}]*\}',      # Struct definition
            r'impl\s+\w+(?:\s+for\s+\w+)?',   # Implementation block
            r'use\s+[\w:]+',                   # Import/use statement
            r'pub\s+(?:fn|struct|enum|mod)',    # Public items
            r'Vec<[^>]+>',                     # Vec generic type
            r'match\s+\w+\s*\{',               # Match expression
            r'#\[\w+(?:\([^)]*\))?\]',          # Attribute macros
            r'\bResult<',                       # Result type
            r'\bOption<',                       # Option type
            r'\bmod\s+\w+',                     # Module declaration
            r'&mut\s+\w+',                      # Mutable references
            r'&\w+',                            # Immutable references
            r'\|[^|]*\|\s*\{',                 # Closure syntax
            r'::\s*[A-Z]\w+',                   # Path to types
            r'::(?:<[^>]+>)?\s*\w+\(',          # Method call with turbofish
            r'enum\s+\w+\s*\{',                 # Enum definition
            r'-\s*>\s*[\w<>:]+',                # Return type arrow
            r'async\s+fn',                      # Async functions
            r'await',                           # Await syntax
            r'move\s*\|',                       # Move closures
            r'trait\s+\w+',                     # Trait definition
            r'\bSome\(',                        # Some variant
            r'\bNone\b',                        # None variant
            r'\bOk\(',                          # Ok variant
            r'\bErr\(',                         # Err variant
            r'\bcrate::\w+',                    # Crate references
            r'pub\(crate\)',                    # Crate visibility
            r'\bdyn\s+\w+',                     # Dynamic dispatch
            r'\bif\s+let\s+Some',                # If let for Option
            r'\bif\s+let\s+Ok'                  # If let for Result
        ]
        return any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns)
        
    @staticmethod
    def detect_csharp(code: str) -> bool:
        """Detect if code is C#."""
        patterns = [
            r'using\s+[\w.]+;',                      # Using statement
            r'namespace\s+[\w.]+',                   # Namespace declaration
            r'(public|private|protected|internal)\s+(class|struct|interface|enum)',  # Type declarations
            r'(public|private|protected|internal)\s+[\w<>\[\]]+\s+\w+\s*\(',  # Method declaration
            r'Console\.(Write|WriteLine)',           # Console output
            r'\bvar\s+\w+\s*=',                     # Var keyword
            r'new\s+\w+\s*\(',                      # Object instantiation
            r'\bawait\s+',                           # Async/await
            r'\btask<',                              # Task object
            r'\bdynamic\b',                          # Dynamic type
            r'\bstring\b',                           # String type
            r'\$".*?\{.*?\}.*?"',                   # String interpolation with $ 
            r'\bIEnumerable<',                       # C# generics
            r'\bList<',                             # C# collections
            r'\bdictionary<',                        # C# collections
            r'\bforeach\s*\(',                      # foreach loops
            r'\bassert\.\w+\(',                     # Unit testing
            r'\[\w+\]',                             # Attributes
            r'\bdelegate\b',                         # Delegates
            r'\bevent\b',                            # Events
            r'\bpartial\b',                          # Partial classes
            r'\bvirtual\b',                          # Virtual methods
            r'\boverride\b',                         # Override methods
            r'\?\s*\w+\s*\??',                      # Nullable types
            r'<\w+>\s*where\s+\w+\s*:',             # Generic constraints
            r'set\s*\{',                            # Property setters
            r'get\s*\{',                            # Property getters
            r'using\s*\(',                          # Using statements with blocks
            r'\bget;\s*set;',                       # Auto-properties
            r'\bselect\s+new\b'                      # LINQ expressions
        ]
        return any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns)
        
    @staticmethod
    def detect_typescript(code: str) -> bool:
        """Detect if code is TypeScript."""
        # TypeScript-specific patterns (not commonly found in other languages)
        ts_patterns = [
            r':\s*[A-Za-z]+(?:<[^>]+>)?\s*(?:=|;|\)|\})',  # Type annotations
            r'interface\s+\w+\s*\{',                 # Interface declaration
            r'class\s+\w+(?:\s+implements|\s+extends)?', # Class with implements or extends
            r'(private|public|protected)\s+\w+',      # Access modifiers
            r'\w+\s*<[^>]+>',                       # Generic types
            r'import\s+\{[^}]+\}\s+from',            # ES6 import
            r'export\s+(interface|class|type|const|let)', # Exports
            r'type\s+\w+\s*=',                       # Type aliases
            r'enum\s+\w+',                            # Enums
            r'@\w+(?:\([^)]*\))?',                    # Decorators
            r'\w+\s*:\s*(?:string|number|boolean|any|void|never|unknown)', # Basic TypeScript types
            r'(?:string|number|boolean|any|void)\[\]', # Array type notation
            r'readonly\s+\w+',                      # Readonly modifier
            r'namespace\s+\w+',                     # TypeScript namespaces
            r'declare\s+(?:var|let|const|function|class|interface)', # Declarations
            r'<[^>]+>\(',                           # Generic function calls
            r'extends\s+\w+<',                      # Generic type inheritance
            r'implements\s+\w+',                    # Interface implementation
            r'as\s+(?:string|number|boolean|any)',  # Type assertions
            r'\?\s*:',                              # Optional properties
            r'\w+\s*\?\s*:',                        # Optional parameters
            r'keyof\s+\w+',                         # keyof operator
            r'typeof\s+\w+',                        # typeof operator
            r'\bReadonly<',                         # Utility types
            r'\bPartial<',                          # Utility types
            r'\bRequired<',                         # Utility types
            r'\bRecord<',                           # Utility types
            r'\|\s*null',                           # Union with null
            r'\|\s*undefined',                      # Union with undefined
            r'\w+\s*&\s*\w+',                       # Intersection types
            r'import\s+type',                       # Import types
            r'export\s+type'                        # Export types
        ]
        
        # Check for TypeScript-specific patterns
        ts_unique = any(re.search(pattern, code, re.IGNORECASE) for pattern in ts_patterns)
        
        # JavaScript patterns for basic JS syntax (TypeScript is a superset of JS)
        js_patterns = [
            r'function\s+\w+\s*\([^)]*\)',  # Function declaration
            r'const\s+\w+\s*=',             # Const declaration
            r'let\s+\w+\s*=',               # Let declaration
            r'var\s+\w+\s*=',               # Var declaration
            r'console\.(log|error|warn)'    # Console methods
        ]
        
        js_general = any(re.search(pattern, code, re.IGNORECASE) for pattern in js_patterns)
        
        # For TypeScript detection, we need to differentiate between object property definitions (which exist in JS)
        # and type annotations (which are unique to TS)
        
        # First, check for specific patterns from other languages to avoid false positives
        
        # Lua-specific patterns
        lua_patterns = [
            r'local\s+\w+\s*=',      # Local variable declarations
            r'function\s*\([^)]*\)\s*', # Anonymous functions
            r'require\(["\']\w+["\'](\))',  # Module imports
            r'end\b',                # End keyword
            r'\bnil\b',              # nil value
            r'\bipairs\(',          # ipairs function
            r'\bpairs\(',          # pairs function
            r'\s*\.\.\.?\s*'       # String concatenation or varargs
        ]
        
        # PHP-specific patterns
        php_patterns = [
            r'<\?php',              # PHP opening tag
            r'\$\w+',              # PHP variables
            r'\-\>\w+',            # PHP object access
            r'public\s+function',  # PHP method declaration
            r'namespace\s+\w+\\',  # PHP namespace with backslash
            r'use\s+\w+\\',        # PHP use statements with backslash
            r'\$this\->'           # PHP $this reference
        ]
        
        # If the code contains clear Lua or PHP indicators, it's not TypeScript
        is_likely_lua = any(re.search(pattern, code) for pattern in lua_patterns)
        is_likely_php = any(re.search(pattern, code) for pattern in php_patterns)
        
        if is_likely_lua or is_likely_php:
            return False
        
        # Check for type annotations in context (not inside object literals)
        type_annotation_patterns = [
            r'function\s+\w+\([^)]*\)\s*:\s*\w+',  # Function return type
            r'const\s+\w+\s*:\s*\w+',  # Variable with type annotation
            r'let\s+\w+\s*:\s*\w+',   # Variable with type annotation
            r':\s*(?:string|number|boolean|any|void|null|undefined)\b', # Basic type annotations
            r':\s*[A-Z][\w]+(?![\w\(])',  # Custom type annotations (type names typically start with capital letter)
            r':\s*[\w\[\]<>|&]+(?=\s*(?:[,\);=]|$))' # Complex type annotations followed by certain delimiters
        ]
        
        has_type_annotation = any(re.search(pattern, code) for pattern in type_annotation_patterns)
        
        # Look for JavaScript syntax indicators
        js_object_literal = re.search(r'\{\s*\w+\s*:\s*[^:\{]+\s*(?:,|\})', code) is not None
        contains_js_imports = re.search(r'import\s+[{\w\s,}]+\s+from\s+["\']', code) is not None
        
        # Only return true for TypeScript-specific patterns or if we have type annotations
        # that are likely to be TypeScript and not other languages
        return ts_unique or (has_type_annotation and (contains_js_imports or js_general) and not (js_object_literal and not ts_unique))
        
    @staticmethod
    def detect_r(code: str) -> bool:
        """Detect if code is R."""
        patterns = [
            r'<-\s*(?:function|\w+)',         # Assignment with <- 
            r'library\([\w\.]+\)',           # Library import
            r'(?:data|read)\.(?:frame|csv|table)', # Data frames
            r'\b(?:if|for|while)\s*\(',     # Control structures
            r'\$\w+',                       # Variable access with $
            r'\bNA\b|\bNULL\b|\bTRUE\b|\bFALSE\b', # R constants
            r'c\(.*?\)',                     # Vector creation with c()
            r'(?:plot|ggplot)\(',            # Plotting functions
            r'\s*#.*$',                      # R comments
            r'%>%',                          # Pipe operator
            r'\bfactor\(',                   # Factor function
            r'\bstr\(',                      # Structure function
            r'\bas\.\w+\(',                  # Type conversion functions
            r'\w+\s*<-\s*\w+\[.+?\]'        # Subsetting with brackets
        ]
        return any(re.search(pattern, code) for pattern in patterns)
        
    @staticmethod
    def detect_perl(code: str) -> bool:
        """Detect if code is Perl."""
        patterns = [
            r'\$\w+',                          # Scalar variables
            r'@\w+',                           # Array variables
            r'%\w+',                           # Hash variables
            r'use\s+[\w:]+\s*;',              # Module imports
            r'\bsub\s+\w+\s*\{',              # Subroutine definition
            r'\bmy\s+(?:\$|@|%)\w+',           # Variable declarations
            r'=~\s*(?:m|s|tr)',                # Regular expression operators
            r'print\s+(?:\$|@|%|")',           # Print statements
            r'(?:if|unless|while|for|foreach)\s*\(',  # Control structures
            r'\{.*?\}.*?\{.*?\}',              # Block structure typical in Perl
            r'->\w+',                          # Method calls
            r'\b(?:shift|pop|push|splice)',     # Array operations
            r';\s*$',                          # Statements ending with semicolon
            r'#.*$',                           # Comments
            r'\bdie\s+',                        # Die statements
            r'\bqw\s*\(',                       # qw() operator
            r'\$_',                             # Special $_ variable
            r'\bdefined\s+(?:\$|@|%)'           # Defined operator
        ]
        return any(re.search(pattern, code) for pattern in patterns)
        
    @staticmethod
    def detect_lua(code: str) -> bool:
        """Detect if code is Lua."""
        patterns = [
            r'\blocal\s+\w+',                    # Local variable declarations
            r'\bfunction\s+\w+(?:\w*\.\w+)*\s*\(', # Function definitions
            r'(?:end|then|do|else)\b',          # Lua keywords
            r'\brequire\s*\(["\w\.\']+\)',       # Module imports
            r'\breturn\s+.+?$',                  # Return statements
            r'\bnil\b',                          # Nil value
            r'\bfor\s+\w+\s*=\s*\d+\s*,\s*\d+', # Numeric for loops
            r'\bfor\s+\w+(?:\s*,\s*\w+)*\s+in\b', # Generic for loops
            r'\bif\s+.+?\s+then\b',              # If statements
            r'\belseif\s+.+?\s+then\b',           # Elseif statements
            r'\btable\.(\w+)\b',                 # Table library functions
            r'\bstring\.(\w+)\b',                # String library functions
            r'\bmath\.(\w+)\b',                  # Math library functions
            r'\bpairs\(\w+\)',                   # Pairs function
            r'\bipairs\(\w+\)',                  # Ipairs function
            r'\btostring\(',                     # Tostring function
            r'\btonumber\(',                     # Tonumber function
            r'\bprint\(',                        # Print function
            r'--.*$',                            # Comments
            r'\[\[.*?\]\]',                      # Multiline strings
            r'\{\s*[\w"\']+\s*=',                # Table initialization
            r'\w+\[\w+\]',                       # Table index access
            r'\w+\.\.\w+'                        # String concatenation
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    
    @staticmethod
    def detect_php(code: str) -> bool:
        """Detect if code is PHP."""
        patterns = [
            r'<\?php',                           # PHP opening tag
            r'\$\w+',                            # Variable with $ prefix
            r'function\s+\w+\s*\(',              # Function definition
            r'echo\s+[\$\w\'\"]+',                # Echo statement
            r'class\s+\w+(?:\s+extends|\s+implements)?', # Class definition
            r'(?:public|private|protected)\s+function', # Class methods
            r'(?:public|private|protected)\s+\$\w+', # Class properties
            r'namespace\s+[\w\\\\]+',              # Namespace declaration
            r'use\s+[\w\\\\]+',                    # Use statement
            r'=>',                               # Array key => value syntax
            r'array\s*\(',                       # Array creation
            r'\[\s*[\'\"]*\w+[\'\"]*\s*\]',        # Array access with []
            r'require(?:_once)?\s*\(',           # Require statements
            r'include(?:_once)?\s*\(',           # Include statements
            r'new\s+\w+',                        # Object instantiation
            r'->',                               # Object property/method access
            r'::',                               # Static property/method access
            r'<?=.*?(?:\?>|$)',                  # Short echo syntax
            r'if\s*\(.+?\)\s*\{',                # If statements
            r'foreach\s*\(\s*\$\w+',             # Foreach loops
            r';$'                                # Statement ending with semicolon
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    
    @staticmethod
    def detect_kotlin(code: str) -> bool:
        """Detect if code is Kotlin."""
        patterns = [
            r'fun\s+\w+\s*\(',                   # Function declaration
            r'val\s+\w+(?:\s*:\s*\w+)?',         # Val declaration
            r'var\s+\w+(?:\s*:\s*\w+)?',         # Var declaration
            r'class\s+\w+(?:\s*\((?:[^)]*)\))?', # Class declaration
            r'package\s+[\w\.]+',                # Package declaration
            r'import\s+[\w\.]+',                 # Import statement
            r'object\s+\w+',                     # Object declaration
            r'interface\s+\w+',                  # Interface declaration
            r'data\s+class',                     # Data class
            r'(?:override|open|abstract|final)\s+fun', # Modified functions
            r'(?:companion|sealed)\s+object',    # Special objects
            r'when\s*\(',                        # When expression
            r'(?:if|else|for|while)\s*\(',       # Control structures
            r'->',                               # Lambda syntax
            r'[\w\.\(\)]+\.\w+\{',               # Extension functions
            r'(?:List|Set|Map)<',                # Generic collections
            r'(?:private|public|internal|protected)', # Visibility modifiers
            r'lateinit\s+var',                   # Lateinit vars
            r'(?:suspend|inline)\s+fun',         # Special function modifiers
            r'@\w+(?:\([^)]*\))?'                # Annotations
        ]
        return any(re.search(pattern, code) for pattern in patterns)

    
    @staticmethod
    def detect_sql(code: str) -> bool:
        """Detect if code is SQL."""
        patterns = [
            r'SELECT\s+[\w\*,\s]+\s+FROM',       # SELECT statement
            r'INSERT\s+INTO\s+\w+',              # INSERT statement
            r'UPDATE\s+\w+\s+SET',               # UPDATE statement
            r'DELETE\s+FROM\s+\w+',              # DELETE statement
            r'CREATE\s+TABLE\s+\w+',             # CREATE TABLE statement
            r'ALTER\s+TABLE\s+\w+',              # ALTER TABLE statement
            r'DROP\s+TABLE\s+\w+',               # DROP TABLE statement
            r'TRUNCATE\s+TABLE\s+\w+',           # TRUNCATE TABLE statement
            r'JOIN\s+\w+\s+ON',                  # JOIN clause
            r'WHERE\s+\w+\s*(?:=|<|>|<=|>=|<>|!=|LIKE|IN)', # WHERE clause
            r'GROUP\s+BY\s+\w+',                 # GROUP BY clause
            r'ORDER\s+BY\s+\w+\s+(?:ASC|DESC)?', # ORDER BY clause
            r'HAVING\s+\w+',                     # HAVING clause
            r'CONSTRAINT\s+\w+',                 # CONSTRAINT declaration
            r'PRIMARY\s+KEY',                    # PRIMARY KEY constraint
            r'FOREIGN\s+KEY',                    # FOREIGN KEY constraint
            r'(?:VARCHAR|INT|INTEGER|FLOAT|DATE|DATETIME|BOOLEAN|TEXT|BLOB)', # Common data types
            r'(?:COUNT|SUM|AVG|MIN|MAX)\s*\(',   # Aggregate functions
            r'CASE\s+WHEN\s+.+?\s+THEN',         # CASE statement
            r'BEGIN\s+TRANSACTION',              # Transaction control
            r'COMMIT',                           # COMMIT statement
            r'ROLLBACK'                          # ROLLBACK statement
        ]
        return any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns)


    def __init__(self):
        """Initialize language detector with detection functions."""
        self.detectors = {
            "Python": self.detect_python,
            "JavaScript": self.detect_javascript,
            "Java": self.detect_java,
            "C++": self.detect_cpp,
            "Julia": self.detect_julia,
            "Go": self.detect_go,
            "Ruby": self.detect_ruby,
            "Swift": self.detect_swift,
            "Rust": self.detect_rust,
            "C#": self.detect_csharp,
            "TypeScript": self.detect_typescript,
            "R": self.detect_r,
            "Perl": self.detect_perl,
            "Lua": self.detect_lua,
            "PHP": self.detect_php,
            "Kotlin": self.detect_kotlin,
            "SQL": self.detect_sql
        }


    def detect_language(self, code: str) -> str:
        """
        Detect the programming language of the given code.
        
        Args:
            code: Code snippet to analyze
            
        Returns:
            Detected language name or None if unknown
        """
        # Initial matching - which language detectors return positive
        matches = {}
        
        # First pass: check which languages match
        for lang, detector in self.detectors.items():
            if detector(code):
                matches[lang] = 0
        
        if not matches:
            return None
            
        # If only one language matches, return it
        if len(matches) == 1:
            return list(matches.keys())[0]
        
        # Improved scoring system with distinctive language features
        # These patterns are selected to be highly distinctive to each language
        # Each pattern is assigned a weight based on how uniquely it identifies a language
        unique_patterns = {
            # C# distinctive features (to differentiate from Java and other languages)
            "C#": [
                (r'using\s+[\w.]+;', 3),                      # Using statement
                (r'namespace\s+[\w.]+', 3),                   # Namespace
                (r'Console\.(Write|WriteLine)', 2),           # Console output
                (r'\bvar\s+\w+\s*=', 3),                     # Var keyword
                (r'\bawait\s+', 4),                           # Async/await
                (r'\btask<', 4),                              # Task object
                (r'\bdynamic\b', 4),                          # Dynamic type
                (r'\$".*?\{.*?\}.*?"', 5),                   # String interpolation with $
                (r'\bIEnumerable<', 4),                       # C# collections
                (r'\bList<', 3),                             # C# collections
                (r'\bforeach\s*\(', 2),                      # foreach loops
                (r'\bget;\s*set;', 5),                       # Auto-properties
                (r'\bselect\s+new\b', 4),                     # LINQ
                (r'\bwhere\s+\w+\s*=', 4),                    # LINQ
                (r'<\w+>\s*where\s+\w+\s*:', 5)                # Generic constraints
            ],
            
            # Rust distinctive features (to differentiate from C++)
            "Rust": [
                (r'fn\s+\w+\s*\(', 3),                        # Function declaration
                (r'let\s+mut\s+\w+', 5),                      # Mutable variable
                (r'impl\s+\w+(?:\s+for\s+\w+)?', 6),           # Implementation
                (r'use\s+[\w:]+', 2),                         # Use statement
                (r'pub\s+(?:fn|struct|enum|mod)', 4),          # Public items
                (r'\bResult<', 5),                           # Result type
                (r'\bOption<', 5),                           # Option type
                (r'\bmod\s+\w+', 4),                         # Module declaration
                (r'&mut\s+\w+', 5),                          # Mutable references
                (r'trait\s+\w+', 6),                         # Trait definition
                (r'\bSome\(', 5),                            # Some variant
                (r'\bNone\b', 5),                            # None variant
                (r'\bOk\(', 5),                              # Ok variant
                (r'\bErr\(', 5),                             # Err variant
                (r'\bcrate::\w+', 5),                        # Crate references
                (r'\bif\s+let\s+Some', 6)                     # If let for Option
            ],
            
            # Swift distinctive features (to differentiate from Kotlin)
            "Swift": [
                (r'import\s+(?:Foundation|UIKit|SwiftUI)', 6), # Swift imports
                (r'@IBOutlet|@IBAction', 8),                  # iOS annotations
                (r'guard\s+let', 6),                         # Guard statement
                (r'\bOptional<', 6),                          # Optional type
                (r'\bas\?', 5),                               # Type casting
                (r'\bas!', 5),                                # Forced type casting
                (r'\?\?', 4),                                 # Nil coalescing
                (r'extension\s+\w+', 4),                      # Extensions
                (r'protocol\s+\w+', 4),                       # Protocols
                (r'convenience\s+init', 6),                    # Convenience init
                (r'required\s+init', 6),                      # Required init
                (r'\bUInt\d*\b', 5),                          # Swift integer types
                (r'\bInt\d*\b', 4),                           # Swift integer types
                (r'\barray<', 3),                             # Swift arrays
                (r'\bdictionary<', 3),                        # Swift dictionaries
                (r'@escaping', 8)                             # Escaping closures
            ],
            
            # TypeScript distinctive features (to differentiate from JavaScript and Python)
            "TypeScript": [
                (r':\s*[A-Za-z]+(?:<[^>]+>)?\s*(?:=|;|\)|\})', 5),  # Type annotations
                (r'interface\s+\w+\s*\{', 6),                 # Interface
                (r'type\s+\w+\s*=', 6),                       # Type aliases
                (r'enum\s+\w+', 5),                            # Enums
                (r'namespace\s+\w+', 6),                     # TypeScript namespaces
                (r'declare\s+(?:var|let|const|function|class|interface)', 7), # Declarations
                (r'as\s+(?:string|number|boolean|any)', 6),  # Type assertions
                (r'\?\s*:', 5),                              # Optional properties
                (r'\w+\s*\?\s*:', 5),                        # Optional parameters
                (r'keyof\s+\w+', 7),                         # keyof operator
                (r'typeof\s+\w+', 6),                        # typeof operator
                (r'\bReadonly<', 7),                         # Utility types
                (r'\bPartial<', 7),                          # Utility types
                (r'\bRequired<', 7),                         # Utility types
                (r'\bRecord<', 7),                           # Utility types
                (r'\w+\s*&\s*\w+', 6),                       # Intersection types
                (r'import\s+type', 8),                       # Import types
                (r'export\s+type', 8)                        # Export types
            ],
            
            # Keep other language patterns but add more weight to distinctive features
            "PHP": [(r'<\?php', 10), (r'\$\w+\s*=', 2), (r'function\s+\w+\s*\(.*?\)\s*\{', 2)],
            "SQL": [(r'(?i)SELECT\s+[\w\*,\s]+\s+FROM', 10), (r'(?i)INSERT\s+INTO', 8), (r'(?i)CREATE\s+TABLE', 8)],
            "Perl": [(r'\buse\s+[\w:]+\s*;', 6), (r'\bmy\s+(?:\$|@|%)', 8), (r'\bperl\b', 10)],
            "Lua": [(r'\blocal\s+\w+', 6), (r'\bfunction\s+\w+(?:\w*\.\w+)*\s*\(', 6), (r'\bend\s*$', 4)],
            "Kotlin": [(r'\bfun\s+\w+\s*\(', 6), (r'\bval\s+\w+(?:\s*:\s*\w+)?', 6), (r'data\s+class', 10)],
            "Ruby": [(r'\bdef\s+\w+\s*(?:\([^)]*\))?\s*$', 6), (r'\bend\b', 4), (r'\bdo\s*\|[^|]*\|', 6)],
            "R": [(r'<-\s*(?:function|\w+)', 8), (r'library\([\w\.]+\)', 8), (r'%>%', 10)],
            "Python": [(r'def\s+\w+\s*\([^)]*\)\s*:', 6), (r'import\s+[\w\s,]+', 4), (r'from\s+[\w.]+\s+import', 6)],
            "JavaScript": [(r'function\s+\w+\s*\([^)]*\)', 4), (r'const\s+\w+\s*=', 3), (r'let\s+\w+\s*=', 3)],
            "Java": [(r'public\s+class\s+\w+', 6), (r'public\s+static\s+void\s+main', 8), (r'System\.(out|err)\.', 6)],
            "C++": [(r'#include\s*<[^>]+>', 6), (r'std::\w+', 8), (r'int\s+main\s*\(', 4)],
            "Julia": [(r'function\s+\w+\s*\([^)]*\)\s*end', 8), (r'module\s+\w+', 6), (r'using\s+\w+', 4)],
            "Go": [(r'package\s+\w+', 6), (r'func\s+\w+\s*\(', 4), (r'import\s*\(', 4)]
        }
        
        # Apply the detailed scoring system
        for lang, patterns in unique_patterns.items():
            if lang in matches:
                for pattern, weight in patterns:
                    if re.search(pattern, code, re.IGNORECASE):
                        matches[lang] += weight
        
        # Additional weighting for core language features
        # C# vs Java disambiguation
        if "C#" in matches and "Java" in matches:
            # C# specific features that are unlikely in Java
            csharp_specific = [
                (r'\$"', 8),                  # String interpolation
                (r'\bvar\b', 6),               # var keyword
                (r'\basync\b', 6),             # async keyword
                (r'\bawait\b', 6),             # await keyword
                (r'\bIEnumerable<', 6),        # C# specific interfaces
                (r'\bget;\s*set;', 8),         # Auto-properties
                (r'\bLINQ\b', 8),              # LINQ
                (r'\busing\s+static', 8)        # using static
            ]
            for pattern, weight in csharp_specific:
                if re.search(pattern, code, re.IGNORECASE):
                    matches["C#"] += weight
            
            # Java specific features that are unlikely in C#
            java_specific = [
                (r'\bimport\s+java\.', 8),       # Java imports
                (r'\bSystem\.out\.print', 6),   # Java System.out
                (r'\bpublic\s+static\s+void\s+main', 8), # Java main method
                (r'\@Override\b', 6),           # Java annotations
                (r'\bextends\s+\w+\s*\{', 6),   # Java inheritance
                (r'\bimplements\s+\w+\s*\{', 6)  # Java interface implementation
            ]
            for pattern, weight in java_specific:
                if re.search(pattern, code, re.IGNORECASE):
                    matches["Java"] += weight
                    
        # Rust vs C++ disambiguation
        if "Rust" in matches and "C++" in matches:
            # Rust specific features that are unlikely in C++
            rust_specific = [
                (r'\bfn\b', 8),                    # fn keyword
                (r'\blet\b', 8),                   # let keyword
                (r'\bmut\b', 8),                   # mut keyword
                (r'\bimpl\b', 8),                  # impl keyword
                (r'\buse\b', 6),                   # use keyword
                (r'\bSome\(', 8),                  # Some variant
                (r'\bNone\b', 8),                  # None variant
                (r'\bResult<', 8),                 # Result type
                (r'\bOption<', 8)                  # Option type
            ]
            for pattern, weight in rust_specific:
                if re.search(pattern, code, re.IGNORECASE):
                    matches["Rust"] += weight
            
            # C++ specific features that are unlikely in Rust
            cpp_specific = [
                (r'#include', 8),                 # C++ include
                (r'std::', 6),                     # C++ std namespace
                (r'\bclass\b', 6),                # class keyword
                (r'\bpublic:\b', 8),              # public: access specifier
                (r'\bprivate:\b', 8),             # private: access specifier
                (r'\bprotected:\b', 8),           # protected: access specifier
                (r'\btypedef\b', 8),              # typedef keyword
                (r'\bnew\b', 4),                  # new keyword
                (r'\bdelete\b', 8)                # delete keyword
            ]
            for pattern, weight in cpp_specific:
                if re.search(pattern, code, re.IGNORECASE):
                    matches["C++"] += weight
                    
        # Swift vs Kotlin disambiguation
        if "Swift" in matches and "Kotlin" in matches:
            # Swift specific features that are unlikely in Kotlin
            swift_specific = [
                (r'\bimport\s+(?:Foundation|UIKit|SwiftUI)', 10), # Swift imports
                (r'\bguard\b', 8),                # guard keyword
                (r'\?\?', 8),                      # Nil coalescing operator
                (r'\bas\?', 8),                    # Optional downcasting
                (r'\bas!', 8),                     # Forced downcasting
                (r'@IBOutlet', 10),                # Interface Builder
                (r'@IBAction', 10),                # Interface Builder
                (r'@objc', 10),                    # Objective-C interop
                (r'\bUIViewController\b', 10)      # UIKit
            ]
            for pattern, weight in swift_specific:
                if re.search(pattern, code, re.IGNORECASE):
                    matches["Swift"] += weight
            
            # Kotlin specific features that are unlikely in Swift
            kotlin_specific = [
                (r'\bdata\s+class', 10),            # Data class
                (r'\bfun\b', 8),                   # fun keyword
                (r'\bval\b', 6),                   # val keyword
                (r'\bvar\b', 4),                   # var keyword
                (r'\bcompanion\s+object', 10),     # Companion object
                (r'\bwhen\b', 8),                  # when expression
                (r'\bcoroutine', 10),              # Coroutines
                (r'\bsuspend\b', 10),              # Suspend functions
                (r'\blateinit\b', 10),             # Late initialization
                (r'\bimport\s+(?:kotlin|androidx|android)', 10) # Kotlin imports
            ]
            for pattern, weight in kotlin_specific:
                if re.search(pattern, code, re.IGNORECASE):
                    matches["Kotlin"] += weight
                    
        # TypeScript vs JavaScript disambiguation (and Python confusion)
        if "TypeScript" in matches and ("JavaScript" in matches or "Python" in matches):
            # TypeScript specific features that are unlikely in JS or Python
            ts_specific = [
                (r':\s*[A-Za-z]+', 8),             # Type annotations
                (r'\binterface\b', 8),             # interface keyword
                (r'\btype\b\s+\w+\s*=', 10),       # type aliases
                (r'\bnamespace\b', 10),            # namespace keyword
                (r'\benum\b', 8),                  # enum keyword
                (r'\bas\s+(?:string|number|boolean|any)', 10), # Type assertions
                (r'\?:\s*', 10),                    # Optional types
                (r'\bReadonly<', 10),              # Utility types
                (r'\w+\s*&\s*\w+', 10),            # Intersection types
                (r'\bimport\s+type', 10),          # Import types
                (r'\[\w+\s*:\s*\w+\]', 10)         # Typed arrays
            ]
            for pattern, weight in ts_specific:
                if re.search(pattern, code, re.IGNORECASE):
                    matches["TypeScript"] += weight
                    # Remove Python if it's a false positive
                    if "Python" in matches and matches["Python"] < matches["TypeScript"]:
                        matches.pop("Python", None)
        
        # Return the language with the highest score
        if matches:
            return max(matches.items(), key=lambda x: x[1])[0]
        
        return None

    def validate_language(self, code: str, expected_lang: str) -> tuple[bool, str]:
        """Validate if code matches the expected programming language."""
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting code validation for {expected_lang}")
        logger.info(f"Code length: {len(code)} characters")
        
        if not code or not expected_lang:
            logger.warning("Empty code or language not specified")
            return True, ""
        
        detector = self.detectors.get(expected_lang)
        if not detector:
            logger.warning(f"No detector found for language: {expected_lang}")
            return True, ""
        
        if detector(code):
            logger.info(f"Code successfully validated as {expected_lang}")
            return True, ""
        
        detected_lang = self.detect_language(code)
        error_msg = f"Code appears to be {detected_lang or 'unknown'} but {expected_lang} was selected"
        logger.error(f"Language validation failed: {error_msg}")
        return False, error_msg 