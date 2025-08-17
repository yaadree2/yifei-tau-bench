# Copyright Sierra

import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

AIRPORTS = [
            "SFO",
            "JFK",
            "LAX",
            "ORD",
            "DFW",
            "DEN",
            "SEA",
            "ATL",
            "MIA",
            "BOS",
            "PHX",
            "IAH",
            "LAS",
            "MCO",
            "EWR",
            "CLT",
            "MSP",
            "DTW",
            "PHL",
            "LGA",
        ]

class ListAllAirports(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any]) -> str:
        cities = [
            "San Francisco",
            "New York",
            "Los Angeles",
            "Chicago",
            "Dallas",
            "Denver",
            "Seattle",
            "Atlanta",
            "Miami",
            "Boston",
            "Phoenix",
            "Houston",
            "Las Vegas",
            "Orlando",
            "Newark",
            "Charlotte",
            "Minneapolis",
            "Detroit",
            "Philadelphia",
            "LaGuardia",
        ]
        return json.dumps({airport: city for airport, city in zip(AIRPORTS, cities)})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_all_airports",
                "description": "List all airports and their cities.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
