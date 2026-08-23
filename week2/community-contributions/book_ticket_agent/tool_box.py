import base64
import json
from travel_api import TravelAPI
from api_key_loader import ApiKeyLoader
from map_generator import MapGenerator
from openai import OpenAI
from typing import Any, Dict, List, Optional
from PIL import Image
import io
from io import BytesIO


# Internal function specs (simple) used to build OpenAI-compatible tools list
_FUNCTION_SPECS: Dict[str, Dict[str, Any]] = {
    "get_flight": {
        "name": "get_flight",
        "description": (
            "Get flight options from the departure airport (origin), destination airport, date and number of adults."
            "Before calling this function, you should have called 'get_airports' to get airport codes for the origin and destination - 2 calls in total. "
            "Call this when client ask to book a flight, for example when client asks 'Book ticket to Paris on 2023-01-01'. If the origin or destination city is missing ask client first to provide it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "origin_location_code": {
                    "type": "string",
                    "description": "IATA code of the origin airport, e.g. 'MAD'",
                },
                "destination_location_code": {
                    "type": "string",
                    "description": "IATA code of the destination airport, e.g. 'ATH'",
                },
                "departure_date": {
                    "type": "string",
                    "description": "Date of departure in 'YYYY-MM-DD'",
                },
                "adults": {
                    "type": "integer",
                    "description": "Number of adult passengers (default 1)",
                }
            },
            "required": ["origin_location_code", "destination_location_code", "departure_date"],
            "additionalProperties": False
        },
    },
    "get_airports": {
        "name": "get_airports",
        "description": (
            "Get airports for a city name using 'city'. Call this to resolve a city to airports."
            "The response contains a list of airport objects. Use the selected airport's 'iataCode' for get_flight."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to search airports for",
                },
            },
            "required": ["city"],
            "additionalProperties": False
        }
    },
    "get_map": {
        "name": "get_map",
        "description": "Generate a Google Static Map PNG for a list of airport/location for given `city`. Call this function when user ask to show city airports on map",
        "parameters": {
            "type": "object",
                "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to search airports for and than show on map",
                },
            },
            "required": ["city"],
            "additionalProperties": False
        }
    },
    "get_boarding_pass": {
        "name": "get_boarding_pass",
        "description": "Generate a boarding pass for a flight. Call this when client asks for boarding pass.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin_location_code": {
                    "type": "string",
                    "description": "IATA code of the origin airport, e.g. 'MAD'",
                },
                "destination_location_code": {
                    "type": "string",
                    "description": "IATA code of the destination airport, e.g. 'ATH'",
                },
                "departure_date": {
                    "type": "string",
                    "description": "Date of departure in 'YYYY-MM-DD'",
                },
                "name": {
                    "type": "string",
                    "description": "Passenger name",
                }
            },
            "required": ["origin_location_code", "destination_location_code", "departure_date", "name"],
            "additionalProperties": False
        },
    }
}


def _to_openai_tools(specs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert simple specs into OpenAI "tools" list schema."""
    tools: List[Dict[str, Any]] = []
    for spec in specs.values():
        tools.append({
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec.get("description", ""),
                "parameters": spec.get("parameters", {"type": "object"}),
            }
        })
    return tools


def _tool_response(tool_call_id: Optional[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "role": "tool",
        "content": json.dumps(payload),
        "tool_call_id": tool_call_id,
    }

def _parse_args(raw_args: Any) -> Dict[str, Any]:
    if isinstance(raw_args, str):
        try:
            return json.loads(raw_args) if raw_args else {}
        except Exception:
            return {}
    if isinstance(raw_args, dict):
        return raw_args
    return {}

def _extract_tool_call(tool_call: Any):
    function = getattr(tool_call, "function", None) or (
        tool_call.get("function") if isinstance(tool_call, dict) else None
    )
    name = getattr(function, "name", None) or (
        function.get("name") if isinstance(function, dict) else None
    )
    raw_args = getattr(function, "arguments", None) or (
        function.get("arguments") if isinstance(function, dict) else None
    )
    call_id = getattr(tool_call, "id", None) or (
        tool_call.get("id") if isinstance(tool_call, dict) else None
    )
    return name, _parse_args(raw_args), call_id


class ToolBox:
    def __init__(self, keys: ApiKeyLoader):
        self.travel_api = TravelAPI(keys.get("client_id"), keys.get("client_secret"))
        self.map_generator = MapGenerator(keys.get("google_map_api_key"))
        self.openai = OpenAI(api_key=keys.get("openai_api_key"))
        self.tools = _to_openai_tools(_FUNCTION_SPECS)
        self._fn_dispatch = {
            "get_flight": self.get_flight,
            "get_airports": self.get_airports,
            "get_map": self.get_map,
        }

    def get_flight(self, origin_location_code, destination_location_code, departure_date, adults=1):
        return self.travel_api.get_flight(origin_location_code, destination_location_code, departure_date,
                                          adults=adults)

    def get_airports(self, city):
        return self.travel_api.get_airport(city)
    
    def get_map(self, city):
        airports = self.travel_api.get_airport(city)
        return airports, self.map_generator.generate(airports)

    def get_toolset(self):
        return self.tools

    def get_boarding_pass(self, origin_location_code, destination_location_code, departure_date, name):
        image_response = self.openai.images.generate(
            model="dall-e-3",
            prompt=f"An image representing a boarding pass from {origin_location_code} to {destination_location_code} for {name} and departure date {departure_date}",
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
        image_base64 = image_response.data[0].b64_json
        image_data = base64.b64decode(image_base64)
        return Image.open(BytesIO(image_data))


    def apply(self, message):
        """Apply tool calls contained in an assistant message and return a list of tool messages."""
        results: List[Dict[str, Any]] = []
        tool_calls = getattr(message, "tool_calls", None) or []
        if not tool_calls:
            return results

        generated_user_message: Optional[str] = None
        image = None

        for tool_call in tool_calls:
            function_name, arguments, call_id = _extract_tool_call(tool_call)

            if function_name == "get_flight":
                origin_location_code = arguments.get("origin_location_code")
                destination_location_code = arguments.get("destination_location_code")
                departure_date = arguments.get("departure_date")
                adults = arguments.get("adults") or 1

                options = self.get_flight(
                    origin_location_code,
                    destination_location_code,
                    departure_date,
                    adults=adults,
                )
                results.append(_tool_response(call_id, {"flight_options": options}))

            elif function_name == "get_boarding_pass":
                origin_location_code = arguments.get("origin_location_code")
                destination_location_code = arguments.get("destination_location_code")
                departure_date = arguments.get("departure_date")
                name = arguments.get("name")
                image = self.get_boarding_pass(origin_location_code, destination_location_code, departure_date, name)
                results.append(_tool_response(call_id, {"boarding_pass": f"boarding pass for {name} from {origin_location_code} to {destination_location_code} on {departure_date}."}))
                if generated_user_message is None:
                    generated_user_message = (
                        f"Here is my boarding pass for {name} from {origin_location_code} to {destination_location_code} on {departure_date}."
                    )

            elif function_name == "get_airports":
                city = arguments.get("city")
                airports = self.get_airports(city)
                results.append(_tool_response(call_id, {"airports": airports}))
                if generated_user_message is None:
                    generated_user_message = (
                        f"Here are the airports in {city}: {airports} Please help me to select one."
                    )

            elif function_name == "get_map":
                city = arguments.get("city")
                try:
                    airports, img_bytes = self.get_map(city)
                    if img_bytes:
                        try:
                            pil_img = Image.open(io.BytesIO(img_bytes))
                            pil_img.load()
                            if pil_img.mode not in ("RGB", "RGBA"):
                                pil_img = pil_img.convert("RGB")
                            image = pil_img
                        except Exception:
                            image = None
                    results.append(_tool_response(call_id, {"airports": airports}))
                    if generated_user_message is None:
                        generated_user_message = (
                            f"Here are the airports in {city}: {airports} Please help me to select one."
                        )
                except Exception as e:
                    results.append(_tool_response(call_id, {"error": f"get_map failed: {str(e)}"}))

            else:
                # Unknown tool: respond so the model can recover gracefully.
                results.append(_tool_response(call_id, {"error": f"Unknown tool: {function_name}"}))

        if generated_user_message:
            results.append({"role": "user", "content": generated_user_message})

        return results, image
