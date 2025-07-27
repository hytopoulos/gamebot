"""Pytest configuration and fixtures for testing the GameBot application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import os
import sys

# Set up test environment variables before importing server
os.environ["OPENAI_API_KEY"] = "test_key"
os.environ["VECTOR_STORE_ID"] = "test_vs_123"
os.environ["HOST"] = "0.0.0.0"
os.environ["PORT"] = "8000"
os.environ["ALLOWED_ORIGINS"] = "*"

# Add the parent directory to the path so we can import server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import server after environment variables are set
with patch('openai.AsyncOpenAI') as mock_openai:
    from server import create_server, main

@pytest.fixture
def mock_openai_client():
    """Fixture to provide a mocked OpenAI client."""
    with patch('server.AsyncOpenAI') as mock_client:
        yield mock_client.return_value

@pytest.fixture
def test_client(mock_openai_client):
    """Fixture to provide a test client with mocked dependencies."""
    # Set up test environment variables
    os.environ["OPENAI_API_KEY"] = "test_key"
    os.environ["VECTOR_STORE_ID"] = "test_vs_123"
    
    # Create the FastMCP instance with the mocked client
    mcp = create_server(mock_openai_client)
    
    # Wrap the FastMCP instance with FastMCPASGIWrapper
    from server import FastMCPASGIWrapper
    asgi_app = FastMCPASGIWrapper(mcp)
    
    # Create an ASGI test client with the wrapped app
    from starlette.testclient import TestClient
    
    # Return test client
    with TestClient(asgi_app) as client:
        yield client

@pytest.fixture
def mock_search_response():
    """Fixture providing a mock search response from OpenAI."""
    class MockDataItem:
        def __init__(self, file_id, filename, content_text):
            self.file_id = file_id
            self.filename = filename
            self.content = [type('obj', (), {'text': content_text})]
    
    class MockResponse:
        def __init__(self, items):
            self.data = items
    
    return MockResponse([
        MockDataItem("file_123", "test_document.txt", "This is a test document content.")
    ])
