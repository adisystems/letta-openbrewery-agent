def ask_state_brewery_mcp(query: str) -> str:
    """
    Queries the MCP server to retrieve brewery-related information for a specific state.

    Args:
        query (str): The user's natural language query (e.g., "How many breweries are in Texas?")

    Returns:
        str: The answer returned from the MCP backend or an error message.
    """
    try:
        response = requests.post(
            "http://localhost:3000/mcp/search",
            json={"query": query},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print("[MCP DEBUG] Response JSON:", data)

        if "answer" in data:
            return data["answer"]
        elif "error" in data:
            return f"Sorry, something went wrong: {data['error']}"
        else:
            return "Sorry, I couldn't find an answer."

    except Exception as e:
        print(f"[MCP ERROR] {str(e)}")
        return "Sorry, I encountered an issue while fetching that data."