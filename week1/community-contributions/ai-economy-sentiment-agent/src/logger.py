"""
Simple logging utility for the AI Economy Sentiment Agent
"""

from config import LOG_LEVEL


class Logger:
    """
    Simple logger that respects LOG_LEVEL from config.
    
    Levels:
    - MINIMAL: Only critical info and results
    - NORMAL: Key milestones and summaries
    - VERBOSE: All debug information
    """
    
    @staticmethod
    def minimal(message):
        """Always shown (critical info, results, errors)"""
        print(message)
    
    @staticmethod
    def normal(message):
        """Shown in NORMAL and VERBOSE mode (key milestones)"""
        if LOG_LEVEL in ["NORMAL", "VERBOSE"]:
            print(message)
    
    @staticmethod
    def verbose(message):
        """Only shown in VERBOSE mode (debug details)"""
        if LOG_LEVEL == "VERBOSE":
            print(message)
    
    @staticmethod
    def error(message):
        """Always shown (errors and warnings)"""
        print(message)


# Convenience instances
log = Logger()

