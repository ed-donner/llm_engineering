# NaijaCode AI

## Overview
NaijaCode AI is an AI-powered coding assistant integrated into the CodeNaija IDE. Currently in beta, launched September 2024. Think of it like GitHub Copilot but trained to understand African tech patterns.

## Features
- **Smart Code Completion**: Suggests code completions as you type, trained on popular African tech stacks and frameworks.
- **Code Explanation**: Highlight any code block and get a plain English (or Pidgin!) explanation of what it does.
- **Bug Detection**: Identifies potential bugs and security vulnerabilities before you ship.
- **API Integration Helper**: Automatically generates boilerplate code for popular African APIs — Paystack, Flutterwave, Africa's Talking, Termii.
- **Documentation Generator**: Generates README files, docstrings, and API documentation from your code.
- **Nigerian Pidgin Mode**: Optional mode where the AI explains code in Nigerian Pidgin English for fun and accessibility.

## Technical Details
- Built on fine-tuned open-source LLMs (based on Code Llama and StarCoder)
- Trained on 500,000+ code repositories from African developers
- Inference runs on NaijaCode's own GPU cluster in Lagos
- Average response time: 200ms for code completions
- Supports Python, JavaScript, TypeScript, Go, Solidity, and Dart

## Pricing
- Included FREE in the Pro and Team tiers of CodeNaija IDE
- Standalone API access: ₦10,000/month for 100,000 API calls

## Current Limitations
- Still in beta — occasional hallucinations in complex multi-file contexts
- Solidity support is experimental
- Only English and Pidgin language support (Yoruba, Igbo, Hausa coming 2025)
