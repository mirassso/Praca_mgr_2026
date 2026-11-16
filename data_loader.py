import pandas as pd
import streamlit as st
from statsbombpy import sb

# 1. Pobieranie listy dostępnych rozgrywek
@st.cache_data(ttl=3600) # Cache na godzinę
def get_competitions():
    """
    Pobiera wszystkie dostępne darmowe rozgrywki ze StatsBomb.
    """
    try:
        comps = sb.competitions()
        return comps
    except Exception as e:
        st.error(f"Błąd podczas pobierania lig: {e}")
        return pd.DataFrame()

# 2. Pobieranie meczów dla konkretnej ligi i sezonu
@st.cache_data(ttl=3600)
def get_matches(competition_id, season_id):
    """
    Pobiera mecze dla podanego competition_id oraz season_id.
    """
    try:
        matches = sb.matches(competition_id=competition_id, season_id=season_id)
        return matches
    except Exception as e:
        st.error(f"Błąd podczas pobierania meczów: {e}")
        return pd.DataFrame()

# 3. Pobieranie zdarzeń (serce nowej aplikacji)
@st.cache_data(ttl=3600)
def get_match_events(match_id):
    """
    Pobiera wszystkie zdarzenia dla danego meczu i spłaszcza współrzędne przestrzenne.
    """
    try:
        # Pobieramy surowe zdarzenia w formie DataFrame
        events = sb.events(match_id=match_id)
        
        # --- SPŁASZCZANIE WSPÓŁRZĘDNYCH (Data Engineering) ---
        # Domyślnie StatsBomb zwraca lokalizację jako listę [X, Y], np. [120.0, 40.0]. 
        # Rozbijamy to na osobne kolumny, by ułatwić pracę modelowi ML i wykresom.
        
        if 'location' in events.columns:
            # Dropna usuwa wiersze bez lokalizacji przed rozbiciem
            locs = events['location'].dropna().apply(pd.Series)
            locs.columns = ['location_x', 'location_y']
            events = events.join(locs)

        # Spłaszczanie punktu końcowego strzału (Shot End Location)
        # Strzały w StatsBomb mają 3 współrzędne [X, Y, Z], gdzie Z to wysokość!
        if 'shot_end_location' in events.columns:
            shot_locs = events['shot_end_location'].dropna().apply(pd.Series)
            # Zabezpieczenie: czasem brakuje osi Z, więc sprawdzamy liczbę kolumn
            if len(shot_locs.columns) == 3:
                shot_locs.columns = ['shot_end_x', 'shot_end_y', 'shot_end_z']
            elif len(shot_locs.columns) == 2:
                shot_locs.columns = ['shot_end_x', 'shot_end_y']
            events = events.join(shot_locs)

        # Spłaszczanie podań (Pass End Location) - przyda się później do modelu xA i map podań
        if 'pass_end_location' in events.columns:
            pass_locs = events['pass_end_location'].dropna().apply(pd.Series)
            pass_locs.columns = ['pass_end_x', 'pass_end_y']
            events = events.join(pass_locs)
            
        return events
        
    except Exception as e:
        st.error(f"Błąd podczas pobierania zdarzeń meczu: {e}")
        return pd.DataFrame()