import streamlit as st
from tabs import dashboard, matches, players, xg_model, ml_analysis
# Importujemy nasz nowy plik:
from data_loader import load_and_clean_data 

st.set_page_config(page_title="Football Analytics", layout="wide")

# Używamy funkcji z data_loader.py
events, ginf = load_and_clean_data()

# Przekazanie danych do zakładek (reszta zostaje bez zmian)
tabs = st.tabs(["🏠 Dashboard", "⚽ Mecze", "👥 Gracze", "🧠 xG Model", "📊 Analiza ML"])

with tabs[0]:
    dashboard.render(events, ginf)

with tabs[1]:
    matches.render(events, ginf)

with tabs[2]:
    players.render(events, ginf)

with tabs[3]:
    xg_model.render(events, ginf)

with tabs[4]:
    ml_analysis.render(events, ginf)
