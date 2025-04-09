# California Breweries AI Agent Lab

Welcome to the Master's Level Laboratory on AI Agents! In this lab, you'll create an intelligent agent that provides comprehensive information about California breweries using the Letta framework and the OpenBreweryDB API.

## Learning Objectives

## Additional Resources

Before starting this lab, we recommend reviewing:
- [Letta Tools Documentation](https://docs.letta.com/guides/agents/tools) - Learn about creating and managing tools in Letta
- [OpenBreweryDB API Documentation](https://www.openbrewerydb.org/documentation) - Understand the brewery data source

## Learning Objectives

By completing this lab, you will:
1. Understand how to create stateful AI agents using the Letta framework
2. Learn to integrate external APIs (OpenBreweryDB) with AI agents
3. Implement custom tools with specific schemas and functionality
4. Work with system prompts to define agent behavior
5. Handle paginated API responses and data transformation

## Prerequisites

- Docker installed on your system
- Python 3.11+ with pip
- Basic understanding of APIs and JSON
- Familiarity with Python programming

## Environment Setup

1. **Start the Letta Server**

```bash
docker run \
-v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
-p 8283:8283 \
-e GEMINI_API_KEY="YOUR_API_KEY_HERE" \
letta/letta:latest
```

2. **Set up the Python Environment**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv venv && source .venv/bin/activate && UV_PROJECT_ENVIRONMENT=.venv uv sync
```

## Lab Overview

This lab implements an AI agent that specializes in providing information about California breweries. The agent can:
- List all breweries in California
- Provide total counts and type breakdowns
- Share detailed information about specific breweries
- Present data in an organized, user-friendly format

## Code Structure Breakdown

### 1. Tool Implementation

The brewery search tool (`california_breweries`) makes paginated requests to the OpenBreweryDB API and processes the data:

```python
def california_breweries(request_heartbeat: bool = False) -> str:
    """
    Get a complete list and count of all breweries in California.
    
    Args:
        request_heartbeat: Request an immediate heartbeat after function execution
    
    Returns:
        JSON string containing all brewery information
    """
```

Key features:
- Handles pagination automatically
- Processes brewery type statistics
- Formats brewery information consistently
- Implements error handling

### 2. Tool Schema Definition

```python
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
        "required": ["request_heartbeat"]
    }
}
```

### 3. System Prompt

The system prompt defines the agent's behavior and capabilities:

```python
system_prompt = """You are a helpful assistant that provides information about California breweries.

You can tell users:
- The complete list of all breweries in California
- The total count of breweries
- Details about each brewery including name, city, type, and website

When providing information, present it in a clear and organized way.
If asked about other states, explain that you specifically focus on California breweries.
"""
```

## Running the Lab

1. **Create the Agent**
```bash
python letta_open_brewery.py
```

2. **Interact with the Agent**
Create a new file `interact_with_agent.py`:

```python
from letta_client import Letta

# Connect to Letta
client = Letta(base_url="http://localhost:8283")

# Replace with your agent ID from the previous step
agent_id = "your_agent_id_here"

# Send a message to the agent
response = client.agents.messages.create(
    agent_id=agent_id,
    messages=[
        {
            "role": "user",
            "content": "How many breweries are there in California?"
        }
    ]
)
```

## Lab Exercises

1. **Basic Implementation**
   - Run the provided code and create your brewery information agent
   - Test basic queries about California breweries
   - Analyze the agent's responses for accuracy and completeness

2. **Enhanced Functionality**
   - Modify the tool to include additional brewery information
   - Add filtering capabilities (e.g., by city or brewery type)
   - Implement sorting functionality for the results

3. **Advanced Features**
   - Add distance calculations between breweries
   - Implement brewery recommendations based on type preferences
   - Create visualizations of brewery distributions

## Understanding the Results

The agent returns data in a structured JSON format:
```json
{
    "total_breweries": <number>,
    "type_breakdown": {
        "micro": <count>,
        "brewpub": <count>,
        // ... other types
    },
    "breweries": [
        {
            "name": "Example Brewery",
            "city": "San Francisco",
            "type": "micro",
            "website": "http://example.com",
            // ... other details
        }
    ]
}
```

## Technical Notes

- The OpenBreweryDB API has a rate limit of 200 results per page
- The tool handles pagination automatically to retrieve all results
- Error handling is implemented for API failures
- The agent maintains context across conversations
- Responses are cached to improve performance

## Troubleshooting

Common issues and solutions:
1. API Rate Limiting: Implement exponential backoff
2. Data Processing: Handle missing or null values gracefully
3. Memory Management: Monitor response sizes with large datasets

## Problem 1

1. Add support for multiple states.
2. Add one more interesting problem that you can solve with this Agent.

