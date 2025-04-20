#!/usr/bin/env python
# coding: utf-8

"""
Display utilities for the Website Summary Tool
"""

from IPython.display import Markdown, display


def display_summary_markdown(summary):
    """
    Display the summary as markdown in Jupyter.
    
    Args:
        summary: The summary to display
    """
    display(Markdown(summary))


def print_validation_result(is_valid, message):
    """
    Print the result of API key validation.
    
    Args:
        is_valid: Whether the API key is valid
        message: The validation message
    """
    print(message)
    return is_valid