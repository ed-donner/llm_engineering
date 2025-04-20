#!/usr/bin/env python
# coding: utf-8

"""
Data models for the Website Summary Tool
"""

class Website:
    """Class to represent a webpage with its content."""
    
    def __init__(self, url, title, text):
        """
        Initialize a Website object with parsed content.
        
        Args:
            url: The URL of the website
            title: The title of the webpage
            text: The parsed text content of the webpage
        """
        self.url = url
        self.title = title
        self.text = text