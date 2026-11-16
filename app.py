import streamlit as st
import pandas as pd
import data_loader as dl
from tabs import dashboard, matches, players, ml_analysis, ml_reports, model_comparison

# Konfiguracja strony musi być na samej górze
st.set_page_config(page_title="Football Analytics", page_icon="⚽", layout="wide")

st.sidebar.title("Wybór Rozgrywek")

# 1. Pobieramy listę rozgrywek ze StatsBomb
comps = dl.get_competitions()

# ==========================================
# MECHANIZM WIELU SEZONÓW
# ==========================================
if not comps.empty:
    unique_competitions = comps['competition_name'].unique()
    selected_comp_name = st.sidebar.selectbox("🏆 1. Wybierz rozgrywki:", unique_competitions)
    
    # Filtrujemy DataFrame, aby zostawić tylko sezony dla wybranej ligi
    available_seasons = comps[comps['competition_name'] == selected_comp_name]
    unique_seasons = available_seasons['season_name'].unique().tolist()
    

    selected_season_names = st.sidebar.multiselect(
        "📅 2. Wybierz sezon(y):", 
        options=unique_seasons, 
        default=[unique_seasons[0]]
    )
    
    st.sidebar.markdown("---")
    
    # 3. Pobieranie meczów dla WSZYSTKICH wybranych sezonów
    if selected_season_names:
        all_matches_list = []
        
        with st.spinner(f"Pobieranie meczów z {len(selected_season_names)} sezonów..."):
            for season in selected_season_names:
                # Szukamy ID dla danego sezonu
                selected_row = available_seasons[available_seasons['season_name'] == season].iloc[0]
                comp_id = selected_row['competition_id']
                season_id = selected_row['season_id']
                
                # Pobieramy mecze i dodajemy do listy
                season_matches = dl.get_matches(comp_id, season_id)
                if not season_matches.empty:
                    all_matches_list.append(season_matches)
        
        # Sklejamy wszystkie pobrane sezony w jeden potężny DataFrame
        if all_matches_list:
            matches_df = pd.concat(all_matches_list, ignore_index=True)
            st.sidebar.success(f"Znaleziono łącznie {len(matches_df)} meczów!")
        else:
            matches_df = pd.DataFrame()
            st.sidebar.warning("Nie znaleziono meczów dla tych kryteriów.")
    else:
        matches_df = pd.DataFrame()
        st.sidebar.info("Wybierz przynajmniej jeden sezon, aby rozpocząć.")
        
else:
    st.sidebar.error("Brak dostępnych rozgrywek z API.")
    matches_df = pd.DataFrame()

# --- NAWIGACJA W ZAKŁADKACH ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Dashboard", "⚽ Analiza meczów", "🏃 Analiza zawodników", "🎯 Przebieg spotkania", "🧠 Raporty taktyczne", "⚖️ Porównanie modeli xG"])

# Jeśli DataFrame jest pusty (brak wybranego sezonu), we wszystkich zakładkach pokazujemy komunikat
if matches_df.empty:
    for tab in [tab1, tab2, tab3, tab4, tab5, tab6]:
        with tab:
            st.info("👈 Wybierz rozgrywki i przynajmniej jeden sezon z menu po lewej stronie, aby załadować dane.")
else:
    # Jeśli są dane, ładujemy zawartość zakładek
    with tab1:
        dashboard.render(matches_df)
    with tab2:
        matches.render(matches_df)
    with tab3:
        players.render(matches_df)
    with tab4:
        ml_analysis.render(matches_df)
    with tab5:
        ml_reports.render(matches_df)
    with tab6:
        model_comparison.render(matches_df)