import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
from unittest.mock import patch
import data_loader as dl

# --- TESTY: POBIERANIE ROZGRYWEK ---
@patch('statsbombpy.sb.competitions')
def test_get_competitions(mock_comp):
    dl.get_competitions.clear() # Czyszczenie cache Streamlit
    mock_comp.return_value = pd.DataFrame({'competition_id': [9, 12], 'competition_name': ['1. Bundesliga', 'Serie A'], 'season_name': ['2023/2024', '2023/2024']})
    df = dl.get_competitions()
    assert not df.empty

@patch('statsbombpy.sb.competitions')
def test_get_competitions_error(mock_comp):
    dl.get_competitions.clear() # Czyszczenie cache Streamlit
    mock_comp.side_effect = Exception("API Timeout")
    df = dl.get_competitions()
    assert df.empty

# --- TESTY: POBIERANIE MECZÓW ---
@patch('statsbombpy.sb.matches')
def test_get_matches(mock_matches):
    dl.get_matches.clear()
    mock_matches.return_value = pd.DataFrame({'match_id': [101, 102], 'home_team': ['Bayern', 'Dortmund'], 'away_team': ['Bochum', 'Leipzig']})
    df = dl.get_matches(competition_id=9, season_id=27)
    assert not df.empty

@patch('statsbombpy.sb.matches')
def test_get_matches_error(mock_matches):
    dl.get_matches.clear()
    mock_matches.side_effect = Exception("API Timeout")
    df = dl.get_matches(9, 27)
    assert df.empty

# --- TESTY: POBIERANIE ZDARZEŃ ---
@patch('statsbombpy.sb.events')
def test_get_match_events(mock_events):
    dl.get_match_events.clear()
    mock_events.return_value = pd.DataFrame({'id': ['uuid-1'], 'type': ['Shot'], 'player': ['Wirtz']})
    df = dl.get_match_events(101)
    assert not df.empty

@patch('statsbombpy.sb.events')
def test_get_match_events_error(mock_events):
    dl.get_match_events.clear()
    mock_events.side_effect = Exception("API Timeout")
    df = dl.get_match_events(101)
    assert df.empty