from letta_client import Letta
import uuid
import os
from pathlib import Path

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

# Enhanced system prompt for the brewery search agent
system_prompt = """You are a helpful assistant that provides information about U.S. breweries.

You can:
- Provide a complete list of all breweries in California using the california_breweries tool
- Answer questions about breweries in other U.S. states using the ask_state_brewery_mcp tool
- Answer questions about total count, types, or top cities for breweries

When responding:
1. Be clear and organized
2. ALWAYS use the appropriate tool when a user asks about breweries in a specific state
3. For questions about California, use the california_breweries tool
4. For questions about ANY OTHER state, use the ask_state_brewery_mcp tool
5. Summarize the information in a user-friendly way

Example: If asked "How many breweries are in Texas?", use the ask_state_brewery_mcp tool and pass the entire question as the query parameter.
When you get information from a tool, always use the send_message tool to show the information to the user.
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
    base_url = "https://api.openbrewerydb.org/v1/breweries"
    params = {
        'by_state': 'california',
        'per_page': 200
    }

    try:
        all_breweries = []
        page = 1
        while True:
            params['page'] = page
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            breweries = response.json()
            if not breweries:
                break
            all_breweries.extend(breweries)
            page += 1
            if page > 20:
                break

        type_counts = {}
        for brewery in all_breweries:
            brewery_type = brewery.get('brewery_type', 'unknown')
            type_counts[brewery_type] = type_counts.get(brewery_type, 0) + 1

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

# Define the tool name and schema for California breweries
tool_schema = {
    "name": "california_breweries",
    "description": "Get a complete list and count of all breweries in California.",
    "parameters": {
        "type": "object",
        "properties": {
            "request_heartbeat": {
                "type": "boolean",
                "description": "Request an immediate heartbeat after function execution."
            }
        },
        "required": []  # Making request_heartbeat optional
    }
}

print("Checking for existing California breweries tool...")
all_tools = client.tools.list()
brewery_tool = next((t for t in all_tools if t.name == "california_breweries"), None)

if brewery_tool:
    print(f"Found existing brewery tool with ID: {brewery_tool.id}")
else:
    print("No existing California breweries tool found. Creating new one...")
    brewery_tool = client.tools.create(
        source_code=brewery_search_code,
        description="Get information about California breweries",
        source_type="python",
        tags=["brewery", "california", "search"],
        json_schema=tool_schema
    )
    print(f"Created California breweries tool with ID: {brewery_tool.id}")

# MCP tool 
print("Checking for existing MCP tool...")

mcp_tool_code = """
import requests

def ask_state_brewery_mcp(query: str) -> str:
    \"\"\"
    Queries the MCP server to retrieve brewery-related information for a specific state.

    Args:
        query (str): The user's natural language query (e.g., "How many breweries are in Texas?")

    Returns:
        str: The answer returned from the MCP backend or an error message.
    \"\"\"
    try:
        # Connect to the locally running FastAPI MCP server
        response = requests.post(
            "http://localhost:3000/invoke",  # Updated to match your working MCP endpoint
            json={"input": query},  # The FastAPI server expects an 'input' key
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print("[MCP DEBUG] Response JSON:", data)
        
        # Extract the output from the MCP response
        if "output" in data:
            return data["output"]
        elif "error" in data:
            return f"Sorry, something went wrong: {data['error']}"
        else:
            return "Sorry, I couldn't find an answer. Unexpected response format."
    except Exception as e:
        print(f"[MCP ERROR] {str(e)}")
        return f"Sorry, I encountered an issue while fetching brewery data. Error: {str(e)}"
"""


mcp_tool_schema = {
    "name": "ask_state_brewery_mcp",
    "description": "Answer questions about breweries in any U.S. state using the MCP backend.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "User's question about breweries in a specific U.S. state (e.g., 'How many breweries are in Texas?')"
            }
        },
        "required": ["query"]
    }
}

mcp_tool = next((t for t in all_tools if t.name == "ask_state_brewery_mcp"), None)

if mcp_tool:
    print(f"Found existing state MCP tool with ID: {mcp_tool.id}")
    # Since there's no update method, we'll delete the existing tool and create a new one
    print(f"Deleting existing MCP tool to recreate it with updated code...")
    try:
        client.tools.delete(mcp_tool.id)
        print(f"Successfully deleted old MCP tool")
        mcp_tool = None
    except Exception as e:
        print(f"Warning: Failed to delete existing MCP tool: {e}")
        print("Will create a new tool with a different name")
        unique_mcp_suffix = str(uuid.uuid4())[:8]
        mcp_tool_schema["name"] = f"ask_state_brewery_mcp_{unique_mcp_suffix}"

# Create a new MCP tool
if mcp_tool is None:
    print("Creating a new MCP tool...")
    mcp_tool = client.tools.create(
        source_code=mcp_tool_code,
        description="Answer state-level brewery questions using MCP",
        source_type="python",
        tags=["brewery", "state", "mcp"],
        json_schema=mcp_tool_schema
    )
    print(f"Created new MCP tool with ID: {mcp_tool.id}")

# Create agent with a new ID every time to avoid conflicts
agent = client.agents.create(
    name=f"brewery_assistant_{unique_suffix}",
    description="An assistant that provides brewery info across U.S. states",
    system=system_prompt,
    memory_blocks=[],
    tools=[tool_schema["name"], mcp_tool_schema["name"]],  # Use the schema names in case we renamed
    model="letta/letta-free",
    embedding="letta/letta-free"
)

# Export the agent schema
schema = client.agents.export_agent_serialized(agent_id=agent.id)
Path(f"{agent.id}.af").write_text(str(schema))
Path(".agent").write_text(agent.id)
print(f"Created Brewery agent with ID: {agent.id}")
print("Agent created successfully!")
print("\nTo test this agent, visit your Letta UI and look for the agent named:")
print(f"brewery_assistant_{unique_suffix}")