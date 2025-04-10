# Copyright Sierra

import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class GetReservationDetails(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], reservation_id: str) -> str:
        reservations = data["reservations"]
        if reservation_id in reservations:
            return json.dumps(reservations[reservation_id])
        return "Error: user not found"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_reservation_details",
                "description": "Get the details of a reservation. The reservation can be past or future.",  # The last sentence is to remind the agent to call this tool even when the reservation is past
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {
                            "type": "string",
                            "description": "The reservation id, such as '8JX2WO'.",
                        },
                    },
                    "required": ["reservation_id"],
                },
            },
        }
