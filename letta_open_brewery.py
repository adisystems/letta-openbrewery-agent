from letta_client import Letta
import uuid
import os

# Connect to Letta
client = Letta(base_url="http://localhost:8283")

# List available models and print them out
available_models = client.models.list_llms()
print("\nAvailable models:")
for i, model in enumerate(available_models):
    print(f"{i+1}. {model.handle} ({model.model_endpoint_type})")
print("\n")

# Generate unique suffixes for tool names
unique_suffix = str(uuid.uuid4())[:8]

# System prompt for the brewery search agent
system_prompt = """You are a helpful assistant that provides information about California breweries.

You can tell users:
- The complete list of all breweries in California
- The total count of breweries
- Details about each brewery including name, city, type, and website

When providing information, present it in a clear and organized way.
If asked about other states, explain that you specifically focus on California breweries.
"""

# Create the brewery search tool with source code
brewery_search_code = """
import requests
import json

def california_breweries(request_heartbeat: bool = False) -> str:
    \"\"\"
    Get a complete list and count of all breweries in California.
    
    Args:
        request_heartbeat: Request an immediate heartbeat after function execution
    
    Returns:
        JSON string containing all brewery information
    \"\"\"
    # Base URL for the OpenBreweryDB API
    base_url = "https://api.openbrewerydb.org/v1/breweries"
    
    # Set parameters for California
    params = {
        'by_state': 'california',
        'per_page': 200  # Get maximum results per page
    }
    
    try:
        all_breweries = []
        page = 1
        
        # Fetch all pages
        while True:
            params['page'] = page
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            breweries = response.json()
            
            if not breweries:
                break
                
            all_breweries.extend(breweries)
            page += 1

        # Count breweries by type
        type_counts = {}
        for brewery in all_breweries:
            brewery_type = brewery.get('brewery_type', 'unknown')
            type_counts[brewery_type] = type_counts.get(brewery_type, 0) + 1

        # Format all breweries
        formatted_breweries = [
            {
                "name": b.get("name"),
                "city": b.get("city"),
                "type": b.get("brewery_type"),
                "website": b.get("website_url"),
                "street": b.get("street"),
                "state": b.get("state"),
                "postal_code": b.get("postal_code"),
                "phone": b.get("phone")
            }
            for b in all_breweries
        ]

        return json.dumps({
            "total_breweries": len(all_breweries),
            "type_breakdown": type_counts,
            "breweries": formatted_breweries
        }, indent=2)
        
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": f"Failed to fetch brewery data: {str(e)}"
        })
"""

# Define the tool name and schema
tool_schema = {
    "name": "california_breweries",
    "description": "Get a complete list and count of all breweries in California.",
    "parameters": {
        "type": "object",
        "properties": {
            "request_heartbeat": {
                "type": "boolean",
                "description": "Request an immediate heartbeat after function execution. Set to `True` if you want to send a follow-up message or run a follow-up function."
            }
        },
        "required": ["request_heartbeat"]
    }
}

# List all tools and look for an existing brewery tool
print("Checking for existing California breweries tool...")
all_tools = client.tools.list()
brewery_tool = None

for tool in all_tools:
    if tool.name == "california_breweries":
        brewery_tool = tool
        print(f"Found existing brewery tool with ID: {tool.id}")
        break

if brewery_tool is None:
    print("No existing California breweries tool found. Creating new one...")
    brewery_tool = client.tools.create(
        source_code=brewery_search_code,
        description="Get information about California breweries",
        source_type="python",
        tags=["brewery", "california", "search"],
        json_schema=tool_schema
    )
    print(f"Created California breweries tool with ID: {brewery_tool.id}")


# Create the agent with required memory_blocks and LLM configuration
agent = client.agents.create(
    name=f"california_brewery_assistant_{unique_suffix}",
    description="An assistant that provides information about California breweries",
    system=system_prompt,
    memory_blocks=[],
    tools=["california_breweries"],
    model="letta/letta-free",
    embedding="letta/letta-free"
)

print(f"Created Brewery agent with ID: {agent.id}")
print("Agent created successfully!")