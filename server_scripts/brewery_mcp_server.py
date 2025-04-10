# brewery_mcp_server.py
import sys
import json
import urllib.parse
import requests

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
brewery_server = FastMCP("OpenBrewery-MCP-Server")

@brewery_server.tool()
def ask_state_brewery_mcp(query: str) -> dict:
    """
    Returns top 5 breweries in the state mentioned in the query.
    """
    try:
        if "in" not in query.lower():
            return {"output": "Please specify a U.S. state in your query."}
        
        state = query.lower().split("in")[-1].strip()
        encoded_state = urllib.parse.quote(state)
        url = f"https://api.openbrewerydb.org/v1/breweries?by_state={encoded_state}&per_page=5"

        response = requests.get(url)
        response.raise_for_status()
        breweries = response.json()

        if not breweries:
            return {"output": f"No breweries found in {state.title()}."}

        names = [b["name"] for b in breweries]
        result = f"Top breweries in {state.title()}:\n" + "\n".join(f"- {name}" for name in names)
        return {"output": result}

    except Exception as e:
        return {"output": f"Error: {str(e)}"}

@brewery_server.prompt()
def explore_breweries() -> str:
    return """
    You are an assistant that helps users discover breweries across the United States.
    
    You can:
    - Search for breweries in any U.S. state by passing the full user query to the `ask_state_brewery_mcp` tool.

    Example questions:
    - "Find breweries in Oregon"
    - "Show top breweries in Michigan"
    - "Are there any breweries in Alaska?"

    Always pass the entire user question to the tool and return a friendly summary of the results.
    """

if __name__ == "__main__":
    brewery_server.run(transport="stdio")