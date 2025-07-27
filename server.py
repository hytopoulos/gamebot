"""
Sample MCP Server for ChatGPT Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's chat and deep research features.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set, Tuple
from dotenv import load_dotenv

import fastapi
from fastapi import FastAPI, Request, Response, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastmcp import FastMCP
from fastmcp.tools import Tool  # ToolResult is not available in this version
from openai import AsyncOpenAI
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from aiohttp import ClientTimeout


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "")

server_instructions = """
This MCP server provides search and document retrieval capabilities
for chat and deep research connectors. Use the search tool to find relevant documents
based on keywords, then use the fetch tool to retrieve complete
document content with citations.
"""


def create_server(openai_client):
    """Create and configure the MCP server with search and fetch tools."""

    # Initialize the FastMCP server
    mcp = FastMCP(
        name="Sample MCP Server",
        instructions=server_instructions,
    )

    # Define security headers middleware as a class
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            return response

    # Add security headers middleware
    mcp.add_middleware(SecurityHeadersMiddleware)
    
    # Health check endpoint as a FastMCP tool
    @mcp.tool()
    async def health_check() -> dict:
        """
        Health check endpoint that returns the server status.
        
        Returns:
            dict: A dictionary containing the server status and metadata.
        """
        # Create a plain dictionary that will be easy to JSON serialize
        result = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "gamebot",
            "version": "1.0.0"
        }
        
        # Convert to a JSON string and back to ensure it's serializable
        # This will raise an exception immediately if there are any serialization issues
        import json
        json.dumps(result)
        
        # Return the result as a plain dictionary
        return result

    @mcp.tool()
    async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for documents using OpenAI Vector Store search.

        This tool searches through the vector store to find semantically relevant matches.
        Returns a list of search results with basic information. Use the fetch tool to get
        complete document content.

        Args:
            query: Search query string. Natural language queries work best for semantic search.

        Returns:
            Dictionary with 'results' key containing list of matching documents.
            Each result includes id, title, text snippet, and optional URL.
        """
        if not query or not query.strip():
            return {"results": []}

        # Search the vector store using OpenAI API
        logger.info(f"Searching {VECTOR_STORE_ID} for query: '{query}'")

        try:
            response = await openai_client.vector_stores.search(
                vector_store_id=VECTOR_STORE_ID,
                query=query,
                with_content=True,
                limit=100  # Max allowed by API
            )

            results = []
            if not hasattr(response, 'data') or not response.data:
                return {"results": []}
            
            for i, item in enumerate(response.data):
                # Extract file_id, filename, and content
                item_id = getattr(item, 'file_id', f"vs_{i}")
                item_filename = getattr(item, 'filename', f"Document {i+1}")

                # Extract text content from the content array
                content_list = getattr(item, 'content', [])
                text_content = ""
                if content_list and len(content_list) > 0:
                    # Get text from the first content item
                    first_content = content_list[0]
                    if hasattr(first_content, 'text'):
                        text_content = first_content.text
                    elif isinstance(first_content, dict):
                        text_content = first_content.get('text', '')

                if not text_content:
                    text_content = "No content available"

                # Create a snippet from content
                text_snippet = text_content[:200] + "..." if len(
                    text_content) > 200 else text_content

                result = {
                    "id": item_id,
                    "title": item_filename,
                    "text": text_snippet,
                    "url": f"https://platform.openai.com/storage/files/{item_id}"
                }

                results.append(result)

        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return {"results": []}
            
        logger.info(f"Vector store search returned {len(results)} results")
        return {"results": results}

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """Fetch document with security checks."""
        if not id or not isinstance(id, str) or not id.startswith("file_"):
            raise HTTPException(
                status_code=400,
                detail="Invalid document ID format"
            )
        """
        Retrieve complete document content by ID for detailed
        analysis and citation. This tool fetches the full document
        content from OpenAI Vector Store. Use this after finding
        relevant documents with the search tool to get complete
        information for analysis and proper citation.

        Args:
            id: File ID from vector store (file-xxx) or local document ID

        Returns:
            Complete document with id, title, full text content,
            optional URL, and metadata

        Raises:
            ValueError: If the specified ID is not found
        """
        if not id:
            raise ValueError("Document ID is required")

        logger.info(f"Fetching content from vector store for file ID: {id}")

        # Fetch file content from vector store
        content_response = await openai_client.vector_stores.files.content(
            vector_store_id=VECTOR_STORE_ID, file_id=id)

        # Get file metadata
        file_info = await openai_client.vector_stores.files.retrieve(
            vector_store_id=VECTOR_STORE_ID, file_id=id)

        # Extract content from paginated response
        file_content = ""
        if hasattr(content_response, 'data') and content_response.data:
            # Combine all content chunks from FileContentResponse objects
            content_parts = []
            for content_item in content_response.data:
                if hasattr(content_item, 'text'):
                    content_parts.append(content_item.text)
            file_content = "\n".join(content_parts)
        else:
            file_content = "No content available"

        # Use filename as title and create proper URL for citations
        filename = getattr(file_info, 'filename', f"Document {id}")

        result = {
            "id": id,
            "title": filename,
            "text": file_content,
            "url": f"https://platform.openai.com/storage/files/{id}",
            "metadata": None
        }

        # Add metadata if available from file info
        if hasattr(file_info, 'attributes') and file_info.attributes:
            result["metadata"] = file_info.attributes

        logger.info(f"Fetched vector store file: {id}")
        return result

    return mcp


def create_openai_client():
    """Create and return an OpenAI client with the configured API key."""
    if not OPENAI_API_KEY:
        logger.error(
            "OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
        )
        raise ValueError("OpenAI API key is required")
    
    return AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        timeout=ClientTimeout(total=30.0)
    )

# Verify Vector Store ID is set
if not VECTOR_STORE_ID:
    logger.error(
        "Vector Store ID not found. Please set VECTOR_STORE_ID environment variable."
    )
    raise ValueError("Vector Store ID is required")

logger.info(f"Using vector store: {VECTOR_STORE_ID}")

# Create the FastMCP server
mcp_server = create_server(create_openai_client())

# Create an ASGI application wrapper for FastMCP
class FastMCPASGIWrapper:
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            await self.handle_http(scope, receive, send)
        elif scope['type'] == 'lifespan':
            # Handle lifespan events for Starlette's TestClient
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
        else:
            raise NotImplementedError(f"Unsupported scope type: {scope['type']}")
    
    async def handle_http(self, scope, receive, send):
        # Get the request body
        body = b''
        if scope['method'] in ['POST', 'PUT', 'PATCH']:
            more_body = True
            while more_body:
                message = await receive()
                body += message.get('body', b'')
                more_body = message.get('more_body', False)
        
        # Parse JSON body if present
        request_data = {}
        if body:
            try:
                request_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                request_data = {}
        
        # Route the request based on path and method
        path = scope['path']
        method = scope['method']
        
        # Default response
        response = {"error": "Not Found"}
        status_code = 404
        
        # Get the tool manager and tools
        tool_manager = self.mcp_server._tool_manager
        tools = {}
        try:
            tools = await tool_manager.get_tools()
        except Exception as e:
            logger.error(f"Error getting tools: {str(e)}")
        
        try:
            # Route to the appropriate tool based on path and method
            if path == '/health' and method == 'GET':
                tool_name = 'health_check'
                tool_args = {}
            elif path == '/tools' and method == 'GET':
                # Return the list of available tools
                tools_list = []
                for tool_name, tool_info in tools.items():
                    tools_list.append({
                        'name': tool_name,
                        'description': tool_info.get('description', ''),
                        'parameters': tool_info.get('parameters', {})
                    })
                response = {'tools': tools_list}
                status_code = 200
                await self._send_json_response(send, response, status_code)
                return
            elif path == '/search' and method == 'POST':
                tool_name = 'search'
                tool_args = request_data
            elif path == '/fetch' and method == 'POST':
                tool_name = 'fetch'
                tool_args = request_data
            elif path in ['/sse', '/'] and method in ['GET', 'POST']:
                # Handle MCP protocol initialization for both /sse and root paths
                # For GET requests, handle SSE connection
                if method == 'GET':
                    # Check if this is an SSE request
                    accept_header = next((v for k, v in scope.get('headers', []) if k == b'accept'), b'').decode().lower()
                    if 'text/event-stream' in accept_header:
                        # Send SSE headers
                        await send({
                            'type': 'http.response.start',
                            'status': 200,
                            'headers': [
                                [b'content-type', b'text/event-stream; charset=utf-8'],
                                [b'cache-control', b'no-cache, no-transform'],
                                [b'connection', b'keep-alive'],
                                [b'access-control-allow-origin', b'*'],
                                [b'access-control-allow-methods', b'GET, POST, OPTIONS'],
                                [b'access-control-allow-headers', b'Content-Type, Authorization'],
                                [b'x-accel-buffering', b'no'],  # Disable buffering for nginx
                                [b'transfer-encoding', b'chunked'],
                            ],
                        })
                        
                        # Send initial SSE event with server info
                        init_event = (
                            'event: init\n'
                            'data: {'
                            '"jsonrpc":"2.0",'
                            '"id":1,'
                            '"result":{'
                            '"capabilities":{"tools":{"allowedTools":["search","fetch"]}},'
                            '"serverInfo":{"name":"GameBot MCP Server","version":"1.0.0"}'
                            '}}\n\n'
                            'event: ready\n'
                            'data: {}\n\n'
                            'event: keepalive\n'
                            'data: {}\n\n'
                        )
                        
                        await send({
                            'type': 'http.response.body',
                            'body': init_event.encode('utf-8'),
                            'more_body': True
                        })
                        
                        # Keep the connection open
                        while True:
                            await asyncio.sleep(15)  # Send keepalive every 15 seconds
                            try:
                                await send({
                                    'type': 'http.response.body',
                                    'body': b'event: keepalive\ndata: {}\n\n',
                                    'more_body': True
                                })
                            except Exception as e:
                                logger.info(f"Client disconnected: {e}")
                                break
                        return
                    else:
                        # Regular JSON response for non-SSE requests
                        response = {
                            'status': 'ok',
                            'server': 'GameBot MCP Server',
                            'version': '1.0.0',
                            'endpoints': {
                                'mcp_initialize': {'method': 'POST', 'path': '/'},
                                'search': {'method': 'POST', 'path': '/search'},
                                'fetch': {'method': 'POST', 'path': '/fetch'},
                                'health': {'method': 'GET', 'path': '/health'}
                            }
                        }
                        await self._send_json_response(send, response, 200)
                        return
                # For POST requests, handle MCP initialization
                elif request_data.get('method') == 'initialize':
                    response = {
                        'jsonrpc': '2.0',
                        'id': request_data.get('id', 1),
                        'result': {
                            'capabilities': {
                                'tools': {
                                    'allowedTools': ['search', 'fetch']
                                }
                            },
                            'serverInfo': {
                                'name': 'GameBot MCP Server',
                                'version': '1.0.0'
                            }
                        }
                    }
                    await self._send_json_response(send, response, 200)
                    return
                else:
                    response = {
                        'jsonrpc': '2.0',
                        'id': request_data.get('id', 1),
                        'error': {
                            'code': -32601,
                            'message': 'Method not found'
                        }
                    }
                    await self._send_json_response(send, response, 200)
                    return
                
                tool_name = None
            else:
                tool_name = None
            
            # If we found a matching tool, call it
            if tool_name and tool_name in tools:
                try:
                    # Call the tool function with the provided arguments
                    tool_result = await tool_manager.call_tool(tool_name, tool_args)
                    
                    # Handle the tool result
                    if tool_result is not None:
                        # If the tool returns a TextContent object, use its content
                        if hasattr(tool_result, 'content'):
                            response = tool_result.content
                            # If content is a list, take the first item if it exists
                            if isinstance(response, list) and len(response) > 0:
                                response = response[0]
                            # If content has a text attribute, use that
                            if hasattr(response, 'text'):
                                response = response.text
                        else:
                            # Otherwise, use the result directly
                            response = tool_result
                    
                    # Ensure we have a valid response
                    if response is None:
                        response = {"status": "error", "message": "No response from tool"}
                        status_code = 500
                    # If response is a string, wrap it in a dict
                    elif isinstance(response, str):
                        try:
                            # Try to parse as JSON first
                            response = json.loads(response)
                        except json.JSONDecodeError:
                            # If not JSON, wrap in a message field
                            response = {"status": "ok", "message": response}
                    # If response is a list, wrap it in a result field
                    elif isinstance(response, list):
                        response = {"status": "ok", "result": response}
                    # If response is already a dict, ensure it has a status field
                    elif isinstance(response, dict):
                        if "status" not in response:
                            response["status"] = "ok"
                    # For any other type, convert to string
                    else:
                        response = {"status": "ok", "result": str(response)}
                    
                    # Add a timestamp if not already present
                    if isinstance(response, dict) and "timestamp" not in response:
                        response["timestamp"] = datetime.utcnow().isoformat()
                    
                    status_code = 200
                    
                except Exception as e:
                    logger.error(f"Error in {tool_name} tool: {str(e)}", exc_info=True)
                    
                    # Default error response
                    response = {
                        "status": "error",
                        "error": f"Error executing {tool_name}: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    status_code = 500
                    
                    # Unwrap the exception to get to the root cause
                    while hasattr(e, '__cause__') and e.__cause__ is not None:
                        e = e.__cause__
                    
                    # Handle Pydantic ValidationError (422)
                    if isinstance(e, PydanticValidationError):
                        status_code = 422  # Unprocessable Entity
                        response['error'] = "Validation error"
                        response['details'] = json.loads(e.json())
                    # Handle FastAPI's HTTPException
                    elif hasattr(e, 'status_code') and hasattr(e, 'detail'):
                        status_code = e.status_code
                        if isinstance(e.detail, (str, dict, list)):
                            response['error'] = e.detail
                        else:
                            response['error'] = str(e.detail)
                    # Handle FastMCP's ToolError
                    elif hasattr(e, 'message') and hasattr(e, 'code'):
                        # Map common error codes to HTTP status codes
                        error_code = getattr(e, 'code', 500)
                        if error_code == 400:  # Bad Request
                            status_code = 400
                        elif error_code == 401:  # Unauthorized
                            status_code = 401
                        elif error_code == 403:  # Forbidden
                            status_code = 403
                        elif error_code == 404:  # Not Found
                            status_code = 404
                        response['error'] = str(e)
                    # Handle FastAPI's RequestValidationError (422)
                    elif hasattr(e, 'errors') and hasattr(e, 'body'):
                        status_code = 422  # Unprocessable Entity
                        response['error'] = "Validation error"
                        response['details'] = e.errors()
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            response = {
                "status": "error",
                "error": f"Internal server error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            status_code = 500
        
        # Send the response
        await self._send_json_response(send, response, status_code)
        
    async def _send_json_response(self, send, data, status_code=200):
        """Helper method to send JSON responses"""
        if not isinstance(data, (str, bytes)):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        await send({
            'type': 'http.response.start',
            'status': status_code,
            'headers': [
                [b'content-type', b'application/json'],
                [b'access-control-allow-origin', b'*'],
                [b'access-control-allow-methods', b'GET, POST, OPTIONS'],
                [b'access-control-allow-headers', b'Content-Type, Authorization'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': data,
        })

# Create the ASGI application
app = FastMCPASGIWrapper(mcp_server)

def main():
    """Main function to start the MCP server."""
    # Get host and port from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    logger.info(f"Starting MCP server on {host}:{port}")
    logger.info("Server will be accessible via SSE transport")

    # Run the FastMCP server
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
