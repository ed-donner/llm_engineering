import re
from typing import List

class EquationExtractor:

    EQUATION_PATTERNS = re.compile(
        "|".join([
            r"\$\$.+?\$\$",                               # LaTeX display math
            r"\\\[.+?\\\]",                               # LaTeX bracket math
            r"\\begin\{(equation|align|gather|multline|cases)\*?\}.*?\\end\{\1\*?\}",
            r"\\frac\{.+?\}\{.+?\}",                      # fractions
            r"(?:\\sum|\\prod|\\int|\\partial)\b",         # operators
            r"[A-Za-z_]+\s*\(.+?\)\s*=\s*\S+",           # f(x) = ...
            r"^.*[=<>≤≥≈∝∈].*\(\d+\)\s*$",               # numbered equations
            r"[OΘΩ]\s*\([^)]+\)",                         # complexity
            r"[a-zA-Z_]+[\^_]\{[^}]+\}",                  # superscript/subscript
            
            r"_[a-zA-Z]+_\s*=\s*\S+",           # _dk_ = 64
            r"sqrt\s*_?\w+",                      # sqrt dk
            r"_[αβγδεϵλμσπθ]_",                  # _β_ , _ϵ_
            r"_[a-zA-Z]+_\s*\(",                  # _P_ ( or _O_ (
            r"_[A-Za-zα-ωΑ-Ω]+_\s*=\s*[^.\n]+",
            r"sqrt\s*_?[A-Za-zα-ωΑ-Ω]+",
            
            r"_O_\s*\(",
            r"\bO\s*\(",
            
            r"\b\d+\s*[·×]\s*10\d+",
        ]),
        re.MULTILINE | re.DOTALL,
    )

    # general-purpose: detect what KIND of math is present
    EQUATION_SEMANTICS = [
        # (pattern to search in equation text, semantic label)
        (r"[OΘΩ]\s*\(", "computational complexity"),
        (r"\\?(?:sum|∑|Σ)", "summation"),
        (r"\\?(?:prod|∏|Π)", "product"),
        (r"\\?(?:int|∫)", "integral"),
        (r"(?:argmax|argmin|max|min)\b", "optimization"),
        (r"(?:log|ln|exp)\b", "logarithmic/exponential"),
        (r"\\?(?:partial|nabla|∇|grad)\b", "gradient/derivative"),
        (r"(?:loss|Loss|\\mathcal\{L\}|L\s*=)", "loss function"),
        (r"[Pp]\s*\(.*\|", "conditional probability"),
        (r"[Pp]\s*\([^)]+\)", "probability"),
        (r"E\s*[\[\(]|\\mathbb\{E\}", "expectation"),
        (r"Var|Cov|σ\^?2|\\sigma", "variance/statistics"),
        (r"\\frac\{", "fraction"),
        (r"[\^_]\{", "indexed/parameterized expression"),
        (r"\bmatrix\b|\\begin\{[pbvBV]?matrix\}", "matrix operation"),
        (r"≤|≥|\\leq|\\geq|<|>", "inequality/bound"),
        (r":=|\\triangleq|\\equiv|\\stackrel", "definition"),
        (r"\\forall|\\exists|∀|∃", "quantified expression"),
        (r"\{.*\\mid.*\}|\{.*\|.*\}", "set notation"),
    ]

    def contains_equation(self, text: str) -> bool:
        return bool(self.EQUATION_PATTERNS.search(text))

    def extract_equation_lines(self, text: str) -> List[str]:
        return [
            line.strip() for line in text.splitlines()
            if line.strip() and self.EQUATION_PATTERNS.search(line)
        ]

    def describe_equations(self, text: str, section_title: str = "") -> str:
        equations = self.extract_equation_lines(text)
        if not equations:
            return ""

        labels = set()
        eq_text = " ".join(equations)
        for pattern, label in self.EQUATION_SEMANTICS:
            if re.search(pattern, eq_text):
                labels.add(label)

        if not labels:
            labels.add("mathematical formula")

        section_part = f" in section '{section_title}'" if section_title else ""
        specifics = ", ".join(sorted(labels))

        return (
            f"This chunk contains equations{section_part} "
            f"involving: {specifics}."
        )

    def augment_for_embedding(self, text: str, section_title: str = "") -> str:
        description = self.describe_equations(text, section_title)
        if not description:
            return ""
        return f"{description}"