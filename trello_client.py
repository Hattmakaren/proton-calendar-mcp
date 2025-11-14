#!/usr/bin/env python3
"""
Trello Client Module
Provides functions to fetch and filter Trello cards by due dates.
"""

import os
from datetime import datetime, date
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from trello import TrelloClient

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class TrelloCardFetcher:
    """Client for fetching and filtering Trello cards."""

    def __init__(self, api_key: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize Trello client.

        Args:
            api_key: Trello API key (defaults to TRELLO_API_KEY env var)
            token: Trello token (defaults to TRELLO_TOKEN env var)
        """
        self.api_key = api_key or os.getenv("TRELLO_API_KEY", "")
        self.token = token or os.getenv("TRELLO_TOKEN", "")

        if not self.api_key or not self.token:
            raise ValueError(
                "Trello API key and token are required. "
                "Set TRELLO_API_KEY and TRELLO_TOKEN environment variables."
            )

        self.client = TrelloClient(
            api_key=self.api_key,
            token=self.token
        )

    def get_boards(self, board_ids: Optional[List[str]] = None) -> List:
        """
        Get Trello boards.

        Args:
            board_ids: Optional list of board IDs to fetch. If None, fetches all boards.

        Returns:
            List of board objects
        """
        all_boards = self.client.list_boards()

        if board_ids:
            return [board for board in all_boards if board.id in board_ids]

        return all_boards

    def get_cards_from_boards(self, board_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Get all cards from specified boards.

        Args:
            board_ids: Optional list of board IDs. If None, uses TRELLO_BOARD_IDS env var.

        Returns:
            List of card dictionaries with formatted data
        """
        if board_ids is None:
            board_ids_str = os.getenv("TRELLO_BOARD_IDS", "")
            board_ids = [bid.strip() for bid in board_ids_str.split(",") if bid.strip()]

        if not board_ids:
            # Get all boards if no specific IDs provided
            boards = self.get_boards()
        else:
            boards = self.get_boards(board_ids)

        all_cards = []
        for board in boards:
            lists = board.list_lists()
            for list_obj in lists:
                if list_obj.closed:
                    continue
                cards = list_obj.list_cards()
                for card in cards:
                    if not card.closed:
                        all_cards.append(self._format_card(card, board, list_obj))

        return all_cards

    def _format_card(self, card, board, list_obj) -> Dict:
        """
        Format a Trello card into a dictionary.

        Args:
            card: Trello card object
            board: Board object the card belongs to
            list_obj: List object the card belongs to

        Returns:
            Formatted card dictionary
        """
        # Parse due date
        due_date = None
        if card.due_date:
            try:
                # Trello due dates are ISO format strings
                if isinstance(card.due_date, str):
                    due_date = datetime.fromisoformat(card.due_date.replace('Z', '+00:00'))
                elif isinstance(card.due_date, datetime):
                    due_date = card.due_date
            except Exception:
                pass

        # Get checklist progress
        checklists = card.checklists
        total_items = 0
        completed_items = 0

        for checklist in checklists:
            items = checklist.items
            total_items += len(items)
            completed_items += sum(1 for item in items if item.get('state') == 'complete')

        # Get labels
        labels = [label.name for label in card.labels if label.name]

        return {
            "id": card.id,
            "name": card.name,
            "description": card.description or "",
            "due_date": due_date,
            "board_name": board.name,
            "list_name": list_obj.name,
            "labels": labels,
            "url": card.url,
            "checklist_total": total_items,
            "checklist_completed": completed_items,
            "has_attachments": len(card.attachments) > 0,
            "member_count": len(card.member_id) if hasattr(card, 'member_id') else 0,
        }

    def filter_cards_by_due_date(
        self,
        cards: List[Dict],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Filter cards by due date range.

        Args:
            cards: List of card dictionaries
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered list of cards
        """
        filtered = []

        for card in cards:
            due_date = card.get("due_date")
            if not due_date:
                continue

            # Make timezone-naive for comparison
            if due_date.tzinfo is not None:
                due_date = due_date.replace(tzinfo=None)

            # Check date range
            if start_date and due_date < start_date:
                continue
            if end_date and due_date > end_date:
                continue

            filtered.append(card)

        # Sort by due date
        filtered.sort(key=lambda x: x["due_date"] if x["due_date"] else datetime.max)
        return filtered

    def get_cards_due_today(self, cards: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Get cards due today.

        Args:
            cards: Optional list of cards to filter. If None, fetches all cards.

        Returns:
            List of cards due today
        """
        if cards is None:
            cards = self.get_cards_from_boards()

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)

        return self.filter_cards_by_due_date(cards, today_start, today_end)

    def get_cards_due_tomorrow(self, cards: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Get cards due tomorrow.

        Args:
            cards: Optional list of cards to filter. If None, fetches all cards.

        Returns:
            List of cards due tomorrow
        """
        if cards is None:
            cards = self.get_cards_from_boards()

        tomorrow_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = tomorrow_start.replace(day=tomorrow_start.day + 1)
        tomorrow_end = tomorrow_start.replace(hour=23, minute=59, second=59)

        return self.filter_cards_by_due_date(cards, tomorrow_start, tomorrow_end)

    def get_overdue_cards(self, cards: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Get overdue cards (due date in the past).

        Args:
            cards: Optional list of cards to filter. If None, fetches all cards.

        Returns:
            List of overdue cards
        """
        if cards is None:
            cards = self.get_cards_from_boards()

        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        overdue = []

        for card in cards:
            due_date = card.get("due_date")
            if not due_date:
                continue

            # Make timezone-naive for comparison
            if due_date.tzinfo is not None:
                due_date = due_date.replace(tzinfo=None)

            if due_date < now:
                overdue.append(card)

        # Sort by due date (oldest first)
        overdue.sort(key=lambda x: x["due_date"] if x["due_date"] else datetime.min)
        return overdue


def get_trello_client() -> Optional[TrelloCardFetcher]:
    """
    Get Trello client if credentials are configured.

    Returns:
        TrelloCardFetcher instance or None if not configured
    """
    try:
        return TrelloCardFetcher()
    except ValueError:
        return None
