"""
Tests for calendar fetching and parsing functionality.
"""

import pytest
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import httpx
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import fetch_calendar, format_event, filter_events_by_date_range


# Sample ICS data for testing
SAMPLE_ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
UID:test-event-1@example.com
DTSTART:20251113T140000Z
DTEND:20251113T160000Z
SUMMARY:Test Meeting
DESCRIPTION:This is a test meeting
LOCATION:Conference Room A
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
UID:test-event-2@example.com
DTSTART:20251114T100000Z
DTEND:20251114T110000Z
SUMMARY:Team Standup
LOCATION:Office
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
UID:test-event-3@example.com
DTSTART:20251120T150000Z
DTEND:20251120T160000Z
SUMMARY:Future Event
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""


@pytest.mark.asyncio
async def test_fetch_calendar_success():
    """Test successful calendar fetching."""
    mock_response = AsyncMock()
    mock_response.content = SAMPLE_ICS.encode('utf-8')
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        calendar = await fetch_calendar("https://example.com/calendar.ics")

        assert calendar is not None
        assert isinstance(calendar, Calendar)
        # Check that we can walk through events
        events = list(calendar.walk('VEVENT'))
        assert len(events) == 3


@pytest.mark.asyncio
async def test_fetch_calendar_http_error():
    """Test calendar fetching with HTTP error."""
    from unittest.mock import Mock

    mock_response = Mock()
    mock_request = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found",
        request=mock_request,
        response=mock_response
    )

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_calendar("https://example.com/calendar.ics")


@pytest.mark.asyncio
async def test_fetch_calendar_invalid_data():
    """Test calendar fetching with invalid ICS data."""
    mock_response = AsyncMock()
    mock_response.content = b"This is not valid ICS data"
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="Failed to parse calendar data"):
            await fetch_calendar("https://example.com/calendar.ics")


def test_format_event():
    """Test event formatting."""
    cal = Calendar.from_ical(SAMPLE_ICS.encode('utf-8'))
    events = list(cal.walk('VEVENT'))

    formatted = format_event(events[0])

    assert formatted["summary"] == "Test Meeting"
    assert formatted["description"] == "This is a test meeting"
    assert formatted["location"] == "Conference Room A"
    assert formatted["status"] == "CONFIRMED"
    assert formatted["uid"] == "test-event-1@example.com"
    assert formatted["start"] is not None
    assert formatted["end"] is not None


def test_format_event_missing_fields():
    """Test formatting an event with missing optional fields."""
    event = Event()
    event.add('summary', 'Minimal Event')
    event.add('dtstart', datetime(2025, 11, 13, 14, 0, 0))

    formatted = format_event(event)

    assert formatted["summary"] == "Minimal Event"
    assert formatted["description"] == ""
    assert formatted["location"] == ""
    assert formatted["start"] is not None


def test_filter_events_by_date_range():
    """Test filtering events by date range."""
    cal = Calendar.from_ical(SAMPLE_ICS.encode('utf-8'))

    # Filter for events on Nov 13-14, 2025
    start_date = datetime(2025, 11, 13, 0, 0, 0)
    end_date = datetime(2025, 11, 14, 23, 59, 59)

    events = filter_events_by_date_range(cal, start_date, end_date)

    # Should get 2 events (Nov 13 and Nov 14)
    assert len(events) == 2
    assert events[0]["summary"] == "Test Meeting"
    assert events[1]["summary"] == "Team Standup"


def test_filter_events_today():
    """Test filtering events for today."""
    # Create a calendar with an event today
    today = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)

    ics_today = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
UID:today-event@example.com
DTSTART:{today.strftime('%Y%m%dT%H%M%S')}
DTEND:{(today + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}
SUMMARY:Today's Event
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""

    cal = Calendar.from_ical(ics_today.encode('utf-8'))

    # Filter for today
    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    events = filter_events_by_date_range(cal, start_of_day, end_of_day)

    assert len(events) == 1
    assert events[0]["summary"] == "Today's Event"


def test_filter_events_no_matches():
    """Test filtering when no events match the date range."""
    cal = Calendar.from_ical(SAMPLE_ICS.encode('utf-8'))

    # Filter for dates with no events
    start_date = datetime(2025, 11, 1, 0, 0, 0)
    end_date = datetime(2025, 11, 10, 23, 59, 59)

    events = filter_events_by_date_range(cal, start_date, end_date)

    assert len(events) == 0


def test_filter_events_sorted():
    """Test that filtered events are sorted by start time."""
    cal = Calendar.from_ical(SAMPLE_ICS.encode('utf-8'))

    # Get all events
    events = filter_events_by_date_range(cal)

    # Check that events are sorted
    for i in range(len(events) - 1):
        assert events[i]["start"] <= events[i + 1]["start"]


@pytest.mark.asyncio
async def test_fetch_calendar_timeout():
    """Test calendar fetching with timeout."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        mock_client.return_value.__aenter__.return_value.get = mock_get

        with pytest.raises(httpx.TimeoutException):
            await fetch_calendar("https://example.com/calendar.ics")


def test_filter_events_all_day():
    """Test filtering all-day events."""
    # Create calendar with all-day event
    ics_all_day = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Calendar//EN
BEGIN:VEVENT
UID:all-day@example.com
DTSTART;VALUE=DATE:20251115
SUMMARY:All Day Event
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""

    cal = Calendar.from_ical(ics_all_day.encode('utf-8'))

    # Filter for Nov 15, 2025
    start_date = datetime(2025, 11, 15, 0, 0, 0)
    end_date = datetime(2025, 11, 15, 23, 59, 59)

    events = filter_events_by_date_range(cal, start_date, end_date)

    assert len(events) == 1
    assert events[0]["summary"] == "All Day Event"
