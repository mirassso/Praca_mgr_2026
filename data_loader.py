import pandas as pd
import streamlit as st

@st.cache_data
def load_and_clean_data():
    # 1. Wczytanie surowych danych
    events = pd.read_csv("data/events.csv", encoding="utf-8")
    ginf = pd.read_csv("data/ginf.csv", encoding="utf-8")

    # 2. Słowniki (na podstawie dictionary.txt)
    event_type_map = {
        0: 'Announcement', 1: 'Attempt (Strzał)', 2: 'Corner (Rożny)', 3: 'Foul (Faul)', 
        4: 'Yellow card', 5: 'Second yellow card', 6: 'Red card', 
        7: 'Substitution (Zmiana)', 8: 'Free kick won', 9: 'Offside (Spalony)', 
        10: 'Hand ball', 11: 'Penalty conceded'
    }
    
    shot_outcome_map = {
        1: 'On target (Celny)', 2: 'Off target (Niecelny)', 3: 'Blocked (Zablokowany)', 4: 'Hit the bar (Słupek/Poprzeczka)'
    }

    # --- MAPOWANIE SEZONÓW ---
    def format_season(year):
        try:
            y = int(year)
            return f"{y-1}/{str(y)[2:]}"
        except:
            return str(year)

    # Ta linijka jest kluczowa:
    ginf['season_label'] = ginf['season'].apply(format_season)

    # 3. Mapowanie wartości na nowe, czytelne kolumny
    # Używamy nowych nazw kolumn (z dopiskiem _name), żeby nie nadpisywać oryginałów
    events['event_type_name'] = events['event_type'].map(event_type_map)
    events['shot_outcome_name'] = events['shot_outcome'].map(shot_outcome_map)
    
    # Dodanie pomocniczej kolumny - czy zdarzenie jest strzałem?
    events['is_shot'] = events['event_type'] == 1

    return events, ginf

