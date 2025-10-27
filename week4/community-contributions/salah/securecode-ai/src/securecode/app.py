"""Main Gradio application."""

import gradio as gr
from .config import Config
from .analyzers import SecurityAnalyzer, PerformanceAnalyzer, FixGenerator, TestGenerator
from .utils.language_detector import detect_language


class SecureCodeApp:
    """Main application class."""

    def __init__(self):
        """Initialize analyzers."""
        self.security_analyzer = SecurityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.fix_generator = FixGenerator()
        self.test_generator = TestGenerator()

    def analyze_security(self, code: str, language: str):
        """Analyze code for security issues."""
        if language == "Auto-detect":
            language = detect_language(code)

        result = ""
        for chunk in self.security_analyzer.analyze_stream(code, language):
            result += chunk
            yield result

    def analyze_performance(self, code: str, language: str):
        """Analyze code for performance issues."""
        if language == "Auto-detect":
            language = detect_language(code)

        result = ""
        for chunk in self.performance_analyzer.analyze_stream(code, language):
            result += chunk
            yield result

    def generate_fix(self, code: str, issues: str, language: str):
        """Generate fixed code."""
        if language == "Auto-detect":
            language = detect_language(code)

        result = ""
        for chunk in self.fix_generator.generate_fix_stream(code, issues, language):
            result += chunk
            yield result

    def generate_tests(self, code: str, language: str):
        """Generate unit tests."""
        if language == "Auto-detect":
            language = detect_language(code)

        result = ""
        for chunk in self.test_generator.generate_tests_stream(code, language):
            result += chunk
            yield result

    def create_interface(self):
        """Create and return the Gradio interface."""
        languages = ["Auto-detect", "Python", "JavaScript", "Java", "C++", "Go", "Rust"]

        with gr.Blocks(title=Config.APP_NAME) as interface:
            gr.Markdown(f"# {Config.APP_NAME}")
            gr.Markdown(
                f"Analyze your code for security vulnerabilities and performance issues "
                f"using AI.\n\n**Current Model:** {Config.get_model_display_name()}"
            )

            with gr.Tab("🔒 Security Analysis"):
                gr.Markdown(
                    "### Detect Security Vulnerabilities\n"
                    "Identifies common security issues like SQL injection, XSS, "
                    "command injection, and more."
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        security_code = gr.Code(
                            label="Paste Your Code Here",
                            language="python",
                            lines=15,
                        )
                        with gr.Row():
                            security_lang = gr.Dropdown(
                                choices=languages,
                                value="Auto-detect",
                                label="Language",
                                scale=2,
                            )
                            security_btn = gr.Button(
                                "🔍 Analyze Security",
                                variant="primary",
                                scale=1,
                            )

                    with gr.Column(scale=2):
                        security_output = gr.Textbox(
                            label="Security Analysis Report",
                            lines=15,
                            max_lines=20,
                        )

                security_btn.click(
                    fn=self.analyze_security,
                    inputs=[security_code, security_lang],
                    outputs=security_output,
                )

            with gr.Tab("⚡ Performance Analysis"):
                gr.Markdown(
                    "### Optimize Code Performance\n"
                    "Analyzes time/space complexity, identifies bottlenecks, "
                    "and suggests optimizations."
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        perf_code = gr.Code(
                            label="Paste Your Code Here",
                            language="python",
                            lines=15,
                        )
                        with gr.Row():
                            perf_lang = gr.Dropdown(
                                choices=languages,
                                value="Auto-detect",
                                label="Language",
                                scale=2,
                            )
                            perf_btn = gr.Button(
                                "🚀 Analyze Performance",
                                variant="primary",
                                scale=1,
                            )

                    with gr.Column(scale=2):
                        perf_output = gr.Textbox(
                            label="Performance Analysis Report",
                            lines=15,
                            max_lines=20,
                        )

                perf_btn.click(
                    fn=self.analyze_performance,
                    inputs=[perf_code, perf_lang],
                    outputs=perf_output,
                )

            with gr.Tab("🔧 Generate Fix"):
                gr.Markdown(
                    "### Auto-Fix Issues\n"
                    "Automatically generates fixed code based on identified security "
                    "or performance issues."
                )

                with gr.Row():
                    with gr.Column():
                        fix_code = gr.Code(
                            label="Original Code",
                            language="python",
                            lines=10,
                        )
                        fix_issues = gr.Textbox(
                            label="Identified Issues (paste analysis report)",
                            lines=5,
                            placeholder="Paste the security or performance analysis here...",
                        )
                        with gr.Row():
                            fix_lang = gr.Dropdown(
                                choices=languages,
                                value="Auto-detect",
                                label="Language",
                                scale=2,
                            )
                            fix_btn = gr.Button(
                                "✨ Generate Fix",
                                variant="primary",
                                scale=1,
                            )

                    with gr.Column():
                        fix_output = gr.Textbox(
                            label="Fixed Code & Explanation",
                            lines=18,
                            max_lines=25,
                        )

                fix_btn.click(
                    fn=self.generate_fix,
                    inputs=[fix_code, fix_issues, fix_lang],
                    outputs=fix_output,
                )

            with gr.Tab("🧪 Generate Tests"):
                gr.Markdown(
                    "### Auto-Generate Unit Tests\n"
                    "Creates comprehensive pytest test cases including happy path, "
                    "edge cases, and error scenarios."
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        test_code = gr.Code(
                            label="Paste Your Code Here",
                            language="python",
                            lines=15,
                        )
                        with gr.Row():
                            test_lang = gr.Dropdown(
                                choices=languages,
                                value="Auto-detect",
                                label="Language",
                                scale=2,
                            )
                            test_btn = gr.Button(
                                "🧪 Generate Tests",
                                variant="primary",
                                scale=1,
                            )

                    with gr.Column(scale=2):
                        test_output = gr.Textbox(
                            label="Generated Unit Tests",
                            lines=15,
                            max_lines=20,
                        )

                test_btn.click(
                    fn=self.generate_tests,
                    inputs=[test_code, test_lang],
                    outputs=test_output,
                )

            gr.Markdown(
                "---\n"
                "**Note:** This tool uses AI for analysis. "
                "Always review suggestions before applying them to production code."
            )

        return interface


def launch():
    """Launch the Gradio app."""
    app = SecureCodeApp()
    interface = app.create_interface()
    interface.launch()


if __name__ == "__main__":
    launch()
