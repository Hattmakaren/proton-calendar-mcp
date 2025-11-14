"""
Tests for Trello integration in the MCP server.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_trello_cards():
    """Create mock Trello cards for testing."""
    today = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    return [
        {
            "id": "card1",
            "name": "Today Task",
            "description": "Task due today",
            "due_date": today,
            "board_name": "Test Board",
            "list_name": "To Do",
            "labels": ["High Priority"],
            "url": "https://trello.com/c/card1",
            "checklist_total": 3,
            "checklist_completed": 1,
            "has_attachments": False,
            "member_count": 0,
        },
        {
            "id": "card2",
            "name": "Tomorrow Task",
            "description": "Task due tomorrow",
            "due_date": tomorrow,
            "board_name": "Test Board",
            "list_name": "In Progress",
            "labels": ["Bug"],
            "url": "https://trello.com/c/card2",
            "checklist_total": 0,
            "checklist_completed": 0,
            "has_attachments": True,
            "member_count": 2,
        },
        {
            "id": "card3",
            "name": "Overdue Task",
            "description": "Task that is overdue",
            "due_date": yesterday,
            "board_name": "Test Board",
            "list_name": "To Do",
            "labels": ["Critical"],
            "url": "https://trello.com/c/card3",
            "checklist_total": 5,
            "checklist_completed": 3,
            "has_attachments": False,
            "member_count": 1,
        },
    ]


@pytest.mark.asyncio
async def test_trello_tools_added_when_configured(mock_trello_cards):
    """Test that Trello tools are added to the tool list when configured."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        # Need to reload the module to pick up the env vars
        import importlib
        import server
        importlib.reload(server)

        tools = await server.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "get_trello_cards_today" in tool_names
        assert "get_trello_cards_tomorrow" in tool_names
        assert "get_trello_overdue_cards" in tool_names
        assert "get_trello_cards_date_range" in tool_names


@pytest.mark.asyncio
async def test_trello_tools_not_added_when_not_configured():
    """Test that Trello tools are not added when not configured."""
    with patch.dict(os.environ, {}, clear=True):
        # Need to reload the module to pick up the cleared env vars
        import importlib
        import server
        importlib.reload(server)

        tools = await server.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "get_trello_cards_today" not in tool_names
        assert "get_trello_cards_tomorrow" not in tool_names
        assert "get_trello_overdue_cards" not in tool_names
        assert "get_trello_cards_date_range" not in tool_names


@pytest.mark.asyncio
async def test_get_trello_cards_today_success(mock_trello_cards):
    """Test getting today's Trello cards."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        import importlib
        import server
        importlib.reload(server)

        # Mock the Trello client
        mock_client = Mock()
        mock_client.get_cards_due_today.return_value = [mock_trello_cards[0]]
        server.TRELLO_CLIENT = mock_client

        result = await server.call_tool("get_trello_cards_today", {})

        assert len(result) == 1
        assert "Today Task" in result[0].text
        assert "Test Board" in result[0].text
        assert "High Priority" in result[0].text


@pytest.mark.asyncio
async def test_get_trello_cards_today_empty(mock_trello_cards):
    """Test getting today's Trello cards when none exist."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        import importlib
        import server
        importlib.reload(server)

        # Mock the Trello client
        mock_client = Mock()
        mock_client.get_cards_due_today.return_value = []
        server.TRELLO_CLIENT = mock_client

        result = await server.call_tool("get_trello_cards_today", {})

        assert len(result) == 1
        assert "No Trello cards due today" in result[0].text


@pytest.mark.asyncio
async def test_get_trello_cards_tomorrow_success(mock_trello_cards):
    """Test getting tomorrow's Trello cards."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        import importlib
        import server
        importlib.reload(server)

        # Mock the Trello client
        mock_client = Mock()
        mock_client.get_cards_due_tomorrow.return_value = [mock_trello_cards[1]]
        server.TRELLO_CLIENT = mock_client

        result = await server.call_tool("get_trello_cards_tomorrow", {})

        assert len(result) == 1
        assert "Tomorrow Task" in result[0].text
        assert "Bug" in result[0].text


@pytest.mark.asyncio
async def test_get_trello_overdue_cards_success(mock_trello_cards):
    """Test getting overdue Trello cards."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        import importlib
        import server
        importlib.reload(server)

        # Mock the Trello client
        mock_client = Mock()
        mock_client.get_overdue_cards.return_value = [mock_trello_cards[2]]
        server.TRELLO_CLIENT = mock_client

        result = await server.call_tool("get_trello_overdue_cards", {})

        assert len(result) == 1
        assert "Overdue Task" in result[0].text
        assert "Critical" in result[0].text
        assert "overdue" in result[0].text.lower()


@pytest.mark.asyncio
async def test_get_trello_overdue_cards_empty(mock_trello_cards):
    """Test getting overdue cards when none exist."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        import importlib
        import server
        importlib.reload(server)

        # Mock the Trello client
        mock_client = Mock()
        mock_client.get_overdue_cards.return_value = []
        server.TRELLO_CLIENT = mock_client

        result = await server.call_tool("get_trello_overdue_cards", {})

        assert len(result) == 1
        assert "No overdue Trello cards" in result[0].text
        assert "Great job" in result[0].text


@pytest.mark.asyncio
async def test_get_trello_cards_date_range_success(mock_trello_cards):
    """Test getting Trello cards for a date range."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        import importlib
        import server
        importlib.reload(server)

        # Mock the Trello client
        mock_client = Mock()
        mock_client.get_cards_from_boards.return_value = mock_trello_cards
        mock_client.filter_cards_by_due_date.return_value = [mock_trello_cards[0], mock_trello_cards[1]]
        server.TRELLO_CLIENT = mock_client

        result = await server.call_tool("get_trello_cards_date_range", {
            "start_date": "2025-11-13",
            "end_date": "2025-11-14"
        })

        assert len(result) == 1
        assert "Today Task" in result[0].text
        assert "Tomorrow Task" in result[0].text


@pytest.mark.asyncio
async def test_trello_tools_error_when_not_configured():
    """Test that Trello tools return error when not configured."""
    with patch.dict(os.environ, {}, clear=True):
        import importlib
        import server
        importlib.reload(server)
        server.TRELLO_CLIENT = None

        result = await server.call_tool("get_trello_cards_today", {})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "not configured" in result[0].text
        assert "TRELLO_API_KEY" in result[0].text
