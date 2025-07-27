"""
Test script for MCP server using OpenAI client
"""
import os
import asyncio
import pytest
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

@pytest.mark.asyncio
async def test_mcp_integration():
    """Test MCP server integration with OpenAI client"""
    print(f"Testing MCP server at: {MCP_SERVER_URL}")
    
    # Skip this test in CI environment
    if os.environ.get('CI') == 'true' and MCP_SERVER_URL == "http://localhost:8000":
        pytest.skip("Skipping integration test in CI environment")
    
    # Initialize the OpenAI client
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    try:
        # Test 1: Basic chat completion with MCP tools
        print("\n=== Testing basic chat completion with MCP ===")
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": "What can you tell me about this MCP server?"}],
            tools=[{
                "type": "mcp",
                "server_url": MCP_SERVER_URL,
                "headers": {
                    "Content-Type": "application/json"
                }
            }],
            tool_choice="auto"
        )
        
        print("\nResponse from OpenAI:")
        print(response.choices[0].message.content)
        
        # Test 2: Test search functionality
        print("\n=== Testing search functionality ===")
        search_response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": "Search for documents about testing"}],
            tools=[{
                "type": "mcp",
                "server_url": MCP_SERVER_URL,
                "headers": {
                    "Content-Type": "application/json"
                },
                "allowed_tools": ["search"]
            }],
            tool_choice={"type": "function", "function": {"name": "search"}}
        )
        
        print("\nSearch results:")
        print(search_response.choices[0].message.tool_calls[0].function.arguments)
        
        # Test 3: Test fetch functionality (if you have document IDs)
        # Replace 'doc_id' with an actual document ID from your search results
        # print("\n=== Testing fetch functionality ===")
        # fetch_response = await client.chat.completions.create(
        #     model="gpt-4-turbo",
        #     messages=[{"role": "user", "content": "Fetch document with ID 'doc_id'"}],
        #     tools=[{
        #         "type": "mcp",
        #         "server_url": MCP_SERVER_URL,
        #         "headers": {
        #             "Content-Type": "application/json"
        #         },
        #         "allowed_tools": ["fetch"]
        #     }],
        #     tool_choice={"type": "function", "function": {"name": "fetch"}}
        # )
        # 
        # print("\nFetched document:")
        # print(fetch_response.choices[0].message.tool_calls[0].function.arguments)
        
    except Exception as e:
        print(f"Error testing MCP integration: {str(e)}")
        raise
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_mcp_integration())
