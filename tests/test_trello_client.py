"""
Tests for Trello client module.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import os

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trello_client import TrelloCardFetcher, get_trello_client


@pytest.fixture
def mock_trello_card():
    """Create a mock Trello card."""
    card = Mock()
    card.id = "card123"
    card.name = "Test Card"
    card.description = "Test description"
    card.due_date = "2025-11-13T14:00:00.000Z"
    card.url = "https://trello.com/c/card123"
    card.closed = False
    card.labels = []
    card.attachments = []
    card.member_id = []
    card.checklists = []
    return card


@pytest.fixture
def mock_trello_board():
    """Create a mock Trello board."""
    board = Mock()
    board.id = "board123"
    board.name = "Test Board"
    return board


@pytest.fixture
def mock_trello_list():
    """Create a mock Trello list."""
    list_obj = Mock()
    list_obj.id = "list123"
    list_obj.name = "To Do"
    list_obj.closed = False
    return list_obj


def test_trello_client_initialization():
    """Test Trello client initialization with credentials."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        client = TrelloCardFetcher()
        assert client.api_key == "test_key"
        assert client.token == "test_token"


def test_trello_client_missing_credentials():
    """Test Trello client raises error without credentials."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Trello API key and token are required"):
            TrelloCardFetcher()


def test_format_card(mock_trello_card, mock_trello_board, mock_trello_list):
    """Test card formatting."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            formatted = client._format_card(mock_trello_card, mock_trello_board, mock_trello_list)

            assert formatted["id"] == "card123"
            assert formatted["name"] == "Test Card"
            assert formatted["description"] == "Test description"
            assert formatted["board_name"] == "Test Board"
            assert formatted["list_name"] == "To Do"
            assert formatted["due_date"] is not None
            assert isinstance(formatted["due_date"], datetime)


def test_format_card_with_checklists(mock_trello_card, mock_trello_board, mock_trello_list):
    """Test card formatting with checklists."""
    # Create mock checklist
    checklist = Mock()
    checklist.items = [
        {"state": "complete", "name": "Item 1"},
        {"state": "incomplete", "name": "Item 2"},
        {"state": "complete", "name": "Item 3"},
    ]
    mock_trello_card.checklists = [checklist]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            formatted = client._format_card(mock_trello_card, mock_trello_board, mock_trello_list)

            assert formatted["checklist_total"] == 3
            assert formatted["checklist_completed"] == 2


def test_format_card_with_labels(mock_trello_card, mock_trello_board, mock_trello_list):
    """Test card formatting with labels."""
    label1 = Mock()
    label1.name = "High Priority"
    label2 = Mock()
    label2.name = "Bug"

    mock_trello_card.labels = [label1, label2]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            formatted = client._format_card(mock_trello_card, mock_trello_board, mock_trello_list)

            assert "High Priority" in formatted["labels"]
            assert "Bug" in formatted["labels"]


def test_filter_cards_by_due_date():
    """Test filtering cards by due date range."""
    cards = [
        {"name": "Card 1", "due_date": datetime(2025, 11, 13, 14, 0)},
        {"name": "Card 2", "due_date": datetime(2025, 11, 14, 10, 0)},
        {"name": "Card 3", "due_date": datetime(2025, 11, 20, 15, 0)},
        {"name": "Card 4", "due_date": None},
    ]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()

            # Filter for Nov 13-14
            start = datetime(2025, 11, 13, 0, 0)
            end = datetime(2025, 11, 14, 23, 59)
            filtered = client.filter_cards_by_due_date(cards, start, end)

            assert len(filtered) == 2
            assert filtered[0]["name"] == "Card 1"
            assert filtered[1]["name"] == "Card 2"


def test_filter_cards_sorted():
    """Test that filtered cards are sorted by due date."""
    cards = [
        {"name": "Card Late", "due_date": datetime(2025, 11, 20, 15, 0)},
        {"name": "Card Early", "due_date": datetime(2025, 11, 13, 10, 0)},
        {"name": "Card Middle", "due_date": datetime(2025, 11, 15, 12, 0)},
    ]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            filtered = client.filter_cards_by_due_date(cards)

            assert filtered[0]["name"] == "Card Early"
            assert filtered[1]["name"] == "Card Middle"
            assert filtered[2]["name"] == "Card Late"


def test_get_overdue_cards():
    """Test getting overdue cards."""
    yesterday = datetime.now() - timedelta(days=1)
    tomorrow = datetime.now() + timedelta(days=1)

    cards = [
        {"name": "Overdue Card", "due_date": yesterday},
        {"name": "Future Card", "due_date": tomorrow},
        {"name": "No Due Date", "due_date": None},
    ]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            overdue = client.get_overdue_cards(cards)

            assert len(overdue) == 1
            assert overdue[0]["name"] == "Overdue Card"


def test_get_cards_due_today():
    """Test getting cards due today."""
    today = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    cards = [
        {"name": "Today Card", "due_date": today},
        {"name": "Yesterday Card", "due_date": yesterday},
        {"name": "Tomorrow Card", "due_date": tomorrow},
    ]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            today_cards = client.get_cards_due_today(cards)

            assert len(today_cards) == 1
            assert today_cards[0]["name"] == "Today Card"


def test_get_trello_client_with_credentials():
    """Test getting Trello client with credentials."""
    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = get_trello_client()
            assert client is not None
            assert isinstance(client, TrelloCardFetcher)


def test_get_trello_client_without_credentials():
    """Test getting Trello client without credentials returns None."""
    with patch.dict(os.environ, {}, clear=True):
        client = get_trello_client()
        assert client is None


def test_format_card_no_due_date(mock_trello_card, mock_trello_board, mock_trello_list):
    """Test formatting card without due date."""
    mock_trello_card.due_date = None

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            formatted = client._format_card(mock_trello_card, mock_trello_board, mock_trello_list)

            assert formatted["due_date"] is None


def test_filter_cards_excludes_none_due_dates():
    """Test that filtering excludes cards with no due date."""
    cards = [
        {"name": "Card with date", "due_date": datetime(2025, 11, 13, 14, 0)},
        {"name": "Card without date", "due_date": None},
    ]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            filtered = client.filter_cards_by_due_date(cards)

            assert len(filtered) == 1
            assert filtered[0]["name"] == "Card with date"


def test_format_card_with_attachments(mock_trello_card, mock_trello_board, mock_trello_list):
    """Test card formatting with attachments."""
    mock_trello_card.attachments = [Mock(), Mock()]

    with patch.dict(os.environ, {"TRELLO_API_KEY": "test_key", "TRELLO_TOKEN": "test_token"}):
        with patch('trello_client.TrelloClient'):
            client = TrelloCardFetcher()
            formatted = client._format_card(mock_trello_card, mock_trello_board, mock_trello_list)

            assert formatted["has_attachments"] is True
