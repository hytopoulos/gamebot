"""
MCP Server implementation using the official MCP Python SDK.
"""
import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, CallToolResult, ClientRequest, ClientNotification
from mcp.server.fastmcp.server import Context
from openai import OpenAI

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

async def search_tool_handler(params: Dict[str, Any], context: Context) -> CallToolResult:
    """
    Search for information using the OpenAI Vector Store.
    
    Args:
        params: Dictionary containing 'query' key with the search query
        context: The MCP context
        
    Returns:
        CallToolResult: Search results
    """
    query = params.get('query', '')
    print(f"Searching for: {query}")
    
    try:
        # Search the vector store
        search_result = client.beta.vector_stores.search(
            vector_store_id=VECTOR_STORE_ID,
            query=query,
            limit=3
        )
        
        if not search_result.data:
            return CallToolResult(content="No results found.")
            
        # Format the results
        results = []
        for i, result in enumerate(search_result.data, 1):
            results.append(f"{i}. {result.metadata.get('title', 'Untitled')}\n{result.metadata.get('text', '')}")
            
        return CallToolResult(content="\n\n".join(results))
        
    except Exception as e:
        error_msg = f"An error occurred while searching: {str(e)}"
        print(error_msg)
        return CallToolResult(error=error_msg)

async def fetch_tool(params: Dict[str, Any], context: Context) -> CallToolResult:
    """
    Fetch content from a URL.
    
    Args:
        session: The MCP session
        params: Dictionary containing 'url' key with the URL to fetch
        
    Returns:
        ToolResult: The fetched content or an error message
    """
    url = params.get('url', '')
    print(f"Fetching URL: {url}")
    return CallToolResult(content=f"Fetched content from {url} (mock implementation)")

def create_mcp_server():
    """Create and configure the MCP server."""
    # Create and configure server first
    server = Server(
        name="GameBot MCP Server",
        version="1.0.0"
    )
    
    # Create and register search tool
    search_tool = Tool(
        name="search",
        description="Search for information in the knowledge base",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        },
        handler=search_tool_handler
    )
    server.register_tool(search_tool)
    
    # Create and register fetch tool
    fetch_tool = Tool(
        name="fetch",
        description="Fetch content from a URL",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch content from"}
            },
            "required": ["url"]
        },
        handler=fetch_tool
    )
    server.register_tool(fetch_tool)
    
    return server

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
