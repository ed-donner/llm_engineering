"""
Autonomous multi-agent system for Africa flight prices.
Reference: week8 agents; domain: week6 adeyemi-kayode (Karosi/africa-flight-prices).
"""

from .agent import Agent
from .flight_deals import FlightRoute, FlightQuote, FlightOpportunity
from .route_scanner_agent import RouteScannerAgent
from .flight_pricer_agent import FlightPricerAgent
from .planning_agent import FlightPlanningAgent
from .messaging_agent import FlightMessagingAgent

__all__ = [
    "Agent",
    "FlightRoute",
    "FlightQuote",
    "FlightOpportunity",
    "RouteScannerAgent",
    "FlightPricerAgent",
    "FlightPlanningAgent",
    "FlightMessagingAgent",
]
