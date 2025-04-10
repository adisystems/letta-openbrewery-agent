from letta_client import Letta
import uuid
import os
from pathlib import Path
import json

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

# System prompt for the question answering agent
system_prompt = """You are a helpful assistant that can answer any question by using an external knowledge source.

You have access to a powerful tool that can connect to OpenAI's API to provide accurate, up-to-date information on virtually any topic.

When using this tool:
1. Formulate clear, specific questions
2. Present the information in a well-organized, easy-to-understand format
3. Cite the source when providing information
4. If the information isn't available, acknowledge the limitations

Your goal is to provide helpful, accurate information while being transparent about your sources.
"""

# Create the question answering tool with source code
question_answering_code = """
import requests
import json
import os
from typing import Optional

def answer_question(question: str, model: str = "gpt-4o", temperature: float = 0.7, request_heartbeat: bool = False) -> str:
    \"\"\"
    Connects to an OpenAI MCP server to answer questions using a specified model.
    
    Args:
        question: The question to be answered
        model: The OpenAI model to use (default: gpt-4o)
        temperature: Controls randomness (0.0-1.0, lower is more deterministic)
        request_heartbeat: Request an immediate heartbeat after function execution
    
    Returns:
        JSON string containing the answer and metadata
    \"\"\"
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return json.dumps({
            "error": "OPENAI_API_KEY environment variable not set. Please set it and try again."
        })
    
    # OpenAI API endpoint
    endpoint = "https://api.openai.com/v1/chat/completions"
    
    # Headers for the request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Data payload
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that provides accurate, factual information."},
            {"role": "user", "content": question}
        ],
        "temperature": temperature
    }
    
    try:
        # Send request to OpenAI API
        response = requests.post(endpoint, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Extract the answer
        answer = result["choices"][0]["message"]["content"]
        
        # Return formatted response
        return json.dumps({
            "question": question,
            "answer": answer,
            "model": model,
            "usage": result.get("usage", {}),
            "timestamp": requests.get("http://worldtimeapi.org/api/ip").json().get("datetime", "Unknown")
        }, indent=2)
        
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": f"Failed to connect to OpenAI API: {str(e)}"
        })
    except (KeyError, IndexError) as e:
        return json.dumps({
            "error": f"Failed to parse API response: {str(e)}"
        })
"""

# Define the tool name and schema
tool_schema = {
    "name": "answer_question",
    "description": "Connect to OpenAI MCP server to answer any question using AI models.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to be answered"
            },
            "model": {
                "type": "string",
                "description": "The OpenAI model to use (e.g., gpt-4o, gpt-4-turbo, gpt-3.5-turbo)",
                "default": "gpt-4o"
            },
            "temperature": {
                "type": "number",
                "description": "Controls randomness (0.0-1.0, lower is more deterministic)",
                "default": 0.7
            },
            "request_heartbeat": {
                "type": "boolean",
                "description": "Request an immediate heartbeat after function execution",
                "default": False
            }
        },
        "required": ["question"]
    }
}

# List all tools and look for an existing question answering tool
print("Checking for existing question answering tool...")
all_tools = client.tools.list()
qa_tool = None

for tool in all_tools:
    if tool.name == "answer_question":
        qa_tool = tool
        print(f"Found existing question answering tool with ID: {tool.id}")
        break

if qa_tool is None:
    print("No existing question answering tool found. Creating new one...")
    qa_tool = client.tools.create(
        source_code=question_answering_code,
        description="Connect to OpenAI MCP server to answer any question",
        source_type="python",
        tags=["openai", "mcp", "question-answering"],
        json_schema=tool_schema
    )
    print(f"Created question answering tool with ID: {qa_tool.id}")

# Create the agent with required memory_blocks and LLM configuration
agent = client.agents.create(
    name=f"question_answering_assistant_{unique_suffix}",
    description="An assistant that can answer any question using OpenAI MCP",
    system=system_prompt,
    memory_blocks=[],
    tools=["answer_question"],
    model="letta/letta-free",
    embedding="letta/letta-free"
)

# Export your agent into a serialized schema object (which you can write to a file)
schema = client.agents.export_agent_serialized(agent_id=agent.id)
Path(f"{agent.id}.af").write_text(str(schema))

print(f"Created Question Answering agent with ID: {agent.id}")
Path(".agent").write_text(agent.id)
print("Agent created successfully!")

# Instructions for setting up the API key
print("\n" + "="*80)
print("IMPORTANT: Before using this agent, you need to set your OpenAI API key.")
print("You can do this by running:")
print("export OPENAI_API_KEY='your-api-key-here'")
print("="*80)