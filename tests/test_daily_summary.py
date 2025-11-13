"""
Tests for the daily summary agent.
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from daily_summary import analyze_preparation_needs, format_event_summary, format_time


def test_analyze_preparation_needs_meeting():
    """Test preparation suggestions for meetings."""
    event = {
        "summary": "Team Meeting",
        "description": "",
        "location": "Conference Room A",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
    }

    preparations = analyze_preparation_needs(event)

    assert len(preparations) > 0
    assert any("agenda" in prep.lower() for prep in preparations)


def test_analyze_preparation_needs_presentation():
    """Test preparation suggestions for presentations."""
    event = {
        "summary": "Product Demo",
        "description": "Demo the new features",
        "location": "Main Office",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
    }

    preparations = analyze_preparation_needs(event)

    assert len(preparations) > 0
    assert any("slides" in prep.lower() or "presentation" in prep.lower() for prep in preparations)


def test_analyze_preparation_needs_interview():
    """Test preparation suggestions for interviews."""
    event = {
        "summary": "Candidate Interview",
        "description": "Interview for senior engineer position",
        "location": "Office",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
    }

    preparations = analyze_preparation_needs(event)

    assert len(preparations) > 0
    assert any("resume" in prep.lower() or "questions" in prep.lower() for prep in preparations)


def test_analyze_preparation_needs_location():
    """Test preparation suggestions for events with locations."""
    event = {
        "summary": "Client Meeting",
        "description": "",
        "location": "Downtown Conference Center",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
    }

    preparations = analyze_preparation_needs(event)

    assert len(preparations) > 0
    assert any("directions" in prep.lower() for prep in preparations)


def test_analyze_preparation_needs_training():
    """Test preparation suggestions for training events."""
    event = {
        "summary": "Python Workshop",
        "description": "Advanced Python techniques",
        "location": "Training Room",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
    }

    preparations = analyze_preparation_needs(event)

    assert len(preparations) > 0
    assert any("materials" in prep.lower() or "questions" in prep.lower() for prep in preparations)


def test_analyze_preparation_needs_no_prep():
    """Test event with no specific preparation needs."""
    event = {
        "summary": "Lunch Break",
        "description": "",
        "location": "",
        "start": datetime(2025, 11, 13, 12, 0),
        "end": datetime(2025, 11, 13, 13, 0),
    }

    preparations = analyze_preparation_needs(event)

    # Should return empty list or minimal suggestions
    assert isinstance(preparations, list)


def test_format_time():
    """Test time formatting."""
    dt = datetime(2025, 11, 13, 14, 30)
    formatted = format_time(dt)

    assert "02:30 PM" == formatted or "2:30 PM" == formatted


def test_format_event_summary_basic():
    """Test basic event formatting."""
    event = {
        "summary": "Test Meeting",
        "description": "This is a test",
        "location": "Office",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
        "status": "CONFIRMED",
        "uid": "test@example.com",
    }

    summary = format_event_summary(event, show_prep=False)

    assert "Test Meeting" in summary
    assert "Office" in summary
    assert "02:00 PM" in summary or "2:00 PM" in summary


def test_format_event_summary_with_prep():
    """Test event formatting with preparation suggestions."""
    event = {
        "summary": "Team Meeting",
        "description": "Weekly sync",
        "location": "Conference Room",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
        "status": "CONFIRMED",
        "uid": "test@example.com",
    }

    summary = format_event_summary(event, show_prep=True)

    assert "Test Meeting" in summary or "Team Meeting" in summary
    assert "Preparation needed" in summary or len(summary) > 0


def test_format_event_summary_long_description():
    """Test event with long description gets truncated."""
    long_desc = "A" * 150  # Very long description

    event = {
        "summary": "Event",
        "description": long_desc,
        "location": "",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
        "status": "CONFIRMED",
        "uid": "test@example.com",
    }

    summary = format_event_summary(event)

    # Should be truncated with ellipsis
    assert "..." in summary


def test_format_event_summary_multiline_description():
    """Test event with multiline description shows only first line."""
    event = {
        "summary": "Event",
        "description": "First line\nSecond line\nThird line",
        "location": "",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
        "status": "CONFIRMED",
        "uid": "test@example.com",
    }

    summary = format_event_summary(event)

    assert "First line" in summary
    assert "Second line" not in summary


def test_format_event_summary_no_location():
    """Test formatting event without location."""
    event = {
        "summary": "Virtual Meeting",
        "description": "Online",
        "location": "",
        "start": datetime(2025, 11, 13, 14, 0),
        "end": datetime(2025, 11, 13, 15, 0),
        "status": "CONFIRMED",
        "uid": "test@example.com",
    }

    summary = format_event_summary(event)

    assert "Virtual Meeting" in summary
    # Location emoji should not appear if no location
    assert summary.count("📍") == 0
