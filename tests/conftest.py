"""Pytest configuration and fixtures for testing the GameBot application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import os
import sys

# Add the parent directory to the path so we can import server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    
    # Create the FastAPI app with the mocked client
    app = create_server(mock_openai_client)
    
    # Return test client
    with TestClient(app.app) as client:
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
