from letta_client import Letta

# Connect to Letta
client = Letta(base_url="http://localhost:8283")

# Replace with your agent ID from the previous step
agent_id = "agent-8babcd1e-0899-4a29-8d9b-664d09912e4f" # Example agent ID

# send a message to the agent
response = client.agents.messages.create(
    agent_id=agent_id,
    messages=[
        {
            "role": "user",
            "content": "Give me the number of breweries in California?"
        }
    ]
)

# the response object contains the messages and usage statistics
print(response)

# if we want to print the usage stats
print(response.usage)

# if we want to print the messages
for message in response.messages:
    print(message)