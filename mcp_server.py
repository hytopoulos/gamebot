"""
MCP Server implementation using the official MCP Python SDK.
"""
import os
import asyncio
import json
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import OpenAI

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

# Create FastMCP instance
mcp = FastMCP(
    name="GameBot MCP Server",
    description="MCP server for GameBot with search and fetch capabilities"
)

# Define tool handlers with @mcp.tool() decorator
@mcp.tool()
async def search(query: str, limit: int = 5) -> str:
    """
    Search for information using the OpenAI Vector Store.
    
    Args:
        query: The search query string
        limit: Maximum number of results to return (default: 5)
        
    Returns:
        Formatted search results as a string
    """
    try:
        # Search the vector store
        search_result = client.beta.vector_stores.search(
            vector_store_id=VECTOR_STORE_ID,
            query=query,
            limit=limit
        )
        
        if not search_result.data:
            return "No results found."
            
        # Format the results
        results = []
        for i, result in enumerate(search_result.data, 1):
            results.append(f"{i}. {result.metadata.get('title', 'Untitled')}\n{result.metadata.get('text', '')}")
            
        return "\n\n".join(results)
        
    except Exception as e:
        error_msg = f"An error occurred while searching: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

@mcp.tool()
async def fetch(url: str) -> str:
    """
    Fetch content from a URL.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        The content of the URL as a string
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        error_msg = f"Error fetching URL: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def create_mcp_server():
    """Create and configure the MCP server."""
    # The tools are already registered via the @mcp.tool() decorator
    # Just return the mcp instance which is our server
    return mcp

# Create the server instance
server = create_mcp_server()

# Expose the ASGI app for Uvicorn/Heroku
app = server.app

if __name__ == "__main__":
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting MCP server on {host}:{port}")
    server.run(host=host, port=port)
