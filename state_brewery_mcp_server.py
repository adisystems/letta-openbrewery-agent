from flask import Flask, request, jsonify
import requests
from collections import Counter
import difflib
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('brewery_mcp_server')

app = Flask(__name__)

US_STATES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware",
    "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
    "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey", "new mexico",
    "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming"
]

def extract_state(query: str) -> str:
    query = query.lower()
    for state in US_STATES:
        if state in query:
            return state
    matches = difflib.get_close_matches(query, US_STATES, n=1, cutoff=0.75)
    return matches[0] if matches else None

def generate_brewery_answer(query):
    state = extract_state(query)
    if not state:
        return "Please mention a U.S. state in your question."

    try:
        logger.info(f"Fetching brewery data for state: {state}")
        breweries = []
        page = 1
        while True:
            response = requests.get(
                "https://api.openbrewerydb.org/v1/breweries",
                params={"by_state": state, "page": page, "per_page": 50},
                timeout=10
            )
            batch = response.json()
            if not batch:
                break
            breweries.extend(batch)
            page += 1
            if page > 20:
                break

        if not breweries:
            return f"No brewery data found for '{state.title()}'."

        if "how many" in query or "number of" in query or "count" in query:
            return f"There are {len(breweries)} breweries in {state.title()}."

        elif "types" in query or "type" in query:
            types = [b.get("brewery_type", "unknown") for b in breweries]
            type_counts = Counter(types)
            type_summary = ", ".join(f"{t} ({c})" for t, c in type_counts.items())
            return f"Brewery types in {state.title()}: {type_summary}."

        elif "cities" in query or "city" in query:
            cities = [b.get("city", "Unknown") for b in breweries]
            city_counts = Counter(cities).most_common(5)
            city_summary = ", ".join(f"{city} ({count})" for city, count in city_counts)
            return f"Top cities in {state.title()} by brewery count: {city_summary}."

        else:
            return f"{state.title()} has {len(breweries)} breweries across {len(set(b.get('city') for b in breweries))} cities."

    except Exception as e:
        logger.error(f"Error retrieving brewery data: {str(e)}")
        return f"Error retrieving data: {str(e)}"

# Simple test endpoint
@app.route('/test', methods=['GET'])
def test():
    logger.info("Test endpoint hit")
    return jsonify({"status": "ok", "message": "MCP server is running correctly"})

# MCP-compatible endpoint with handshake support
@app.route('/call', methods=['POST'])
def call_tool():
    try:
        logger.info(f"Received request to /call endpoint")
        logger.info(f"Headers: {request.headers}")
        
        # Get the request data
        data = request.get_json()
        logger.info(f"Request Body: {data}")
        
        # Handle MCP handshake
        if request.headers.get("X-MCP-HANDSHAKE", "") == "true":
            logger.info("Responding to handshake request")
            return jsonify({
                "name": "state_brewery_search",
                "description": "Answer questions about breweries in any U.S. state",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "A natural language query mentioning a U.S. state"
                        }
                    },
                    "required": ["input"]
                }
            })

        # Process the query
        query = data.get("input", "")
        logger.info(f"Processing query: {query}")
        result = generate_brewery_answer(query)
        logger.info(f"Generated result: {result}")
        
        # Return the response
        return jsonify({"output": result})
    except Exception as e:
        logger.error(f"Error in /call endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Optional dev endpoint
@app.route('/mcp/search', methods=['POST'])
def debug_search():
    try:
        logger.info("Debug endpoint /mcp/search hit")
        data = request.get_json()
        query = data.get("query", "")
        logger.info(f"Debug query: {query}")
        result = generate_brewery_answer(query)
        logger.info(f"Debug result: {result}")
        return jsonify({"answer": result})
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting MCP brewery server on 0.0.0.0:3000...")
    app.run(host='0.0.0.0', port=3000, debug=True)