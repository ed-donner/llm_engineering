import sys
import os
import argparse
from dotenv import load_dotenv

# Ensure root folder and src are in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(override=True)

from src.factory import ProviderFactory
from src.code_generator import CodeGenerator
from src.compiler import CppCompiler

def handle_qa(args):
    print(f"Connecting to provider: {args.provider} using model: {args.model}...")
    try:
        provider = ProviderFactory.get_provider(args.provider)
        response, latency = provider.generate(
            model_id=args.model,
            prompt=args.prompt,
            system_prompt=f"You are operating in expertise domain: {args.expertise}."
        )
        print("\n--- Response ---")
        print(response)
        print("----------------")
        print(f"Latency: {latency:.2f}s")
    except Exception as e:
        print(f"Error executing Q&A query: {e}", file=sys.stderr)
        sys.exit(1)

def handle_translate(args):
    if not os.path.exists(args.file):
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Reading Python code from {args.file}...")
    with open(args.file, "r", encoding="utf-8") as f:
        py_code = f.read()

    print(f"Translating using provider: {args.provider}, model: {args.model}...")
    try:
        generator = CodeGenerator(args.provider, args.model)
        cpp_code, latency = generator.translate(py_code)
        
        # Save translated code
        out_file = args.out or (os.path.splitext(args.file)[0] + ".cpp")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(cpp_code)
        print(f"C++ translation saved to: {out_file} (Latency: {latency:.2f}s)")
    except Exception as e:
        print(f"Error during code translation: {e}", file=sys.stderr)
        sys.exit(1)

def handle_compile(args):
    if not os.path.exists(args.file):
        print(f"C++ file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
        
    with open(args.file, "r", encoding="utf-8") as f:
        cpp_code = f.read()

    print(f"Compiling C++ file {args.file}...")
    compiler = CppCompiler()
    result = compiler.compile_and_run(cpp_code)
    
    print(f"Method: {result['method'].upper()} | Success: {result['success']}")
    if not result['success']:
        print("\n--- Compilation Error ---")
        print(result['compilation_error'])
        sys.exit(1)
        
    print("\n--- Execution Output (stdout) ---")
    print(result['execution_stdout'] if result['execution_stdout'] else "[no output]")
    if result['execution_stderr']:
        print("\n--- Execution Error (stderr) ---")
        print(result['execution_stderr'])
        
    if args.asm and result['assembly']:
        print("\n--- Assembly Output ---")
        print(result['assembly'][:800] + "\n... [truncated]")

def main():
    parser = argparse.ArgumentParser(description="Questher v3 - AI Developer Command Line Tool")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")

    # Q&A Command
    qa_parser = subparsers.add_parser("qa", help="Ask a technical question")
    qa_parser.add_argument("prompt", help="Question prompt text")
    qa_parser.add_argument("--provider", default="OpenRouter", help="AI Provider name")
    qa_parser.add_argument("--model", default="google/gemini-2.5-pro", help="Model ID")
    qa_parser.add_argument("--expertise", default="Software Development", help="Expertise Persona")

    # Translate Command
    trans_parser = subparsers.add_parser("translate", help="Translate Python script to C++17")
    trans_parser.add_argument("file", help="Python input file path")
    trans_parser.add_argument("--out", "-o", help="Output C++ path (default is python_name.cpp)")
    trans_parser.add_argument("--provider", default="OpenRouter", help="AI Provider name")
    trans_parser.add_argument("--model", default="google/gemini-2.5-pro", help="Model ID")

    # Compile Command
    comp_parser = subparsers.add_parser("compile", help="Compile and run C++ code")
    comp_parser.add_argument("file", help="C++ source file path")
    comp_parser.add_argument("--asm", action="store_true", help="Print compiled assembly")

    args = parser.parse_args()

    if args.command == "qa":
        handle_qa(args)
    elif args.command == "translate":
        handle_translate(args)
    elif args.command == "compile":
        handle_compile(args)

if __name__ == "__main__":
    main()
