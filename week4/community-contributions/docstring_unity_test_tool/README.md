# Docstring & Unit Test Generator

A simple tool that helps you add clear docstrings and generate realistic pytest-style unit tests for Python projects using large language models. 

Check the Full Repository: https://github.com/Jsrodrigue/docstring_unity_test_generator

What it does
- Scans your Python code to find functions and classes.
- Uses an LLM to write helpful docstrings and to create matching unit tests.
- Adds only the docstring into your source files (it does not rewrite your code).
- Creates test files under a `tests/` folder that mirror your project layout.
- Lets you review generated docstrings before saving them.

Why use it
- Save time: automatically produce documentation and tests so developers can focus on logic.
- Improve quality: get consistent, readable docstrings and test examples that reflect your code.
- Safer changes: review and accept docstring generator.

How it works (simple flow)
1. The tool finds items in your code (functions and classes).
2. For each item, it asks an LLM to write a docstring or a pytest test.
3. You review the suggested content and approve or edit it.
4. Approved docstrings are inserted into source files; generated tests are written under `tests/`.

Main features (at a glance)
- Safe docstring insertion only (no full-file rewrites).
- Mirrored test tree under `tests/`.
- Lightweight web UI to preview suggestions and a CLI for automation.
- Modular LLM layer so models can be swapped if needed.



Demo video (CLI usage)
- Short demo: [![Watch the demo](https://img.youtube.com/vi/4-6kulni4_Y/maxresdefault.jpg)](https://youtu.be/4-6kulni4_Y)

Notes
- This repository is a practical project demonstrating how LLMs can assist with documentation and testing. Changes are suggested and remain under user control.

License
MIT — see the LICENSE file in the repository for details.

