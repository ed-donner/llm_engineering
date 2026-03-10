"""
Week 8 Multi-Agent System
Organized agent implementations with confidence-aware ensemble
"""

from .base_agent import Agent
from .specialist_agent import SpecialistAgent
from .frontier_agent import FrontierAgent
from .ensemble_agent import EnsembleAgent

__all__ = [
    'Agent',
    'SpecialistAgent',
    'FrontierAgent',
    'EnsembleAgent',
]
