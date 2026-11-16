import streamlit as st
import pandas as pd
import numpy as np
import data_loader as dl

# --- POMOCNICZA FUNKCJA DO GŁĘBOKIEJ ANALIZY ---
@st.cache_data(show_spinner=False)
def generate_advanced_stats(matches_df):
    all_events = []
    
    # Zbieranie zdarzeń ze wszystkich dostępnych meczów
    for match_id in matches_df['match_id']:
        ev = dl.get_match_events(match_id)
        if not ev.empty:
            all_events.append(ev)

    if not all_events:
        return pd.DataFrame(), pd.DataFrame()

    events_df = pd.concat(all_events, ignore_index=True)

    # Filtracja głównych typów zdarzeń
    shots = events_df[events_df['type'] == 'Shot'].copy()
    passes = events_df[events_df['type'] == 'Pass'].copy()
    defensive = events_df[events_df['type'].isin(['Interception', 'Block', 'Clearance', 'Duel'])].copy()

    # --- 1. STATYSTYKI ZAWODNIKÓW ---
    
    # Gole
    goals = shots[shots['shot_outcome'] == 'Goal'].groupby(['player', 'team']).size().reset_index(name='Gole')
    
    # xG (Suma oczekiwanych goli)
    if 'shot_statsbomb_xg' in shots.columns:
        xg = shots.groupby(['player', 'team'])['shot_statsbomb_xg'].sum().reset_index(name='xG')
    else:
        xg = pd.DataFrame(columns=['player', 'team', 'xG'])

    # Kluczowe podania (Podania kończące się strzałem)
    key_passes = passes[passes.get('pass_shot_assist') == True].groupby(['player', 'team']).size().reset_index(name='Kluczowe Podania')

    # Akcje defensywne
    def_actions = defensive.groupby(['player', 'team']).size().reset_index(name='Akcje Defensywne')

    # Łączenie w jedną tabelę
    player_stats = goals.merge(xg, on=['player', 'team'], how='outer')\
                        .merge(key_passes, on=['player', 'team'], how='outer')\
                        .merge(def_actions, on=['player', 'team'], how='outer').fillna(0)

    # --- 2. STATYSTYKI DRUŻYNOWE ---
    if 'shot_statsbomb_xg' in shots.columns:
        team_xg = shots.groupby('team')['shot_statsbomb_xg'].sum().reset_index()
        
        # Zliczanie rozegranych meczów na drużynę
        home_counts = matches_df['home_team'].value_counts()
        away_counts = matches_df['away_team'].value_counts()
        team_matches = home_counts.add(away_counts, fill_value=0).reset_index()
        team_matches.columns = ['team', 'mecze']

        team_stats = team_xg.merge(team_matches, on='team', how='left')
        team_stats['xG / mecz'] = team_stats['shot_statsbomb_xg'] / team_stats['mecze']
        team_stats = team_stats.sort_values(by='xG / mecz', ascending=False)
    else:
        team_stats = pd.DataFrame()

    return player_stats, team_stats

# --- GŁÓWNY WIDOK DASHBOARDU ---
def render(matches_df):
    st.title("📊 Football Analytics Dashboard")
    st.markdown("---")
    
    if matches_df.empty:
        st.warning("Brak danych dla wybranych rozgrywek.")
        return

    # ==========================================
    # 1. BŁYSKAWICZNE KPI
    # ==========================================
    col1, col2, col3, col4 = st.columns(4)
    
    total_matches = len(matches_df)
    total_home_goals = matches_df['home_score'].sum()
    total_away_goals = matches_df['away_score'].sum()
    total_goals = total_home_goals + total_away_goals
    avg_goals = total_goals / total_matches if total_matches > 0 else 0
    
    col1.metric("🏟️ Rozegrane mecze", total_matches)
    col2.metric("⚽ Suma Goli", total_goals)
    col3.metric("📈 Średnia goli / mecz", f"{avg_goals:.2f}")
    col4.metric("🏠 Gole Gospodarzy", total_home_goals)

    st.markdown("---")

    # ==========================================
    # 2. AUTOMATYCZNA TABELA PUNKTOWA
    # ==========================================
    st.markdown("### 🏆 Tabela Ligowa (Na podstawie wczytanych wyników)")
    
    teams = pd.concat([matches_df['home_team'], matches_df['away_team']]).unique()
    table = []
    
    for t in teams:
        home_games = matches_df[matches_df['home_team'] == t]
        away_games = matches_df[matches_df['away_team'] == t]
        
        wins = len(home_games[home_games['home_score'] > home_games['away_score']]) + len(away_games[away_games['away_score'] > away_games['home_score']])
        draws = len(home_games[home_games['home_score'] == home_games['away_score']]) + len(away_games[away_games['away_score'] == away_games['home_score']])
        losses = len(home_games[home_games['home_score'] < home_games['away_score']]) + len(away_games[away_games['away_score'] < away_games['home_score']])
        
        goals_for = home_games['home_score'].sum() + away_games['away_score'].sum()
        goals_against = home_games['away_score'].sum() + away_games['home_score'].sum()
        pts = wins * 3 + draws

        table.append({
            'Drużyna': t, 'Mecze': len(home_games)+len(away_games),
            'Pkt': pts, 'Z': wins, 'R': draws, 'P': losses,
            'Bramki': f"{goals_for}:{goals_against}", 'Bilans': goals_for - goals_against
        })

    table_df = pd.DataFrame(table).sort_values(by=['Pkt', 'Bilans'], ascending=[False, False]).reset_index(drop=True)
    table_df.index = table_df.index + 1
    
    # Wyświetlanie tabeli (z drobnym formatowaniem)
    st.dataframe(table_df, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 3. ZAAWANSOWANA ANALIZA LIGI (ON-DEMAND)
    # ==========================================
    st.markdown("### 🔎 Analiza Ligi")
    
    # Inicjalizacja stanu w pamięci (aby tabele nie znikały po interakcji z nimi)
    if "run_deep_analysis" not in st.session_state:
        st.session_state.run_deep_analysis = False
        
    # Używamy przycisku głównego, który zmienia stan w pamięci sesji
    if st.button("🚀 Uruchom analizę zaawansowaną (Wymaga przetworzenia logów z całego sezonu)", type="primary"):
        st.session_state.run_deep_analysis = True
    
    if st.session_state.run_deep_analysis:
        with st.spinner("Pobieranie i kompilowanie danych przestrzennych (to może potrwać kilkanaście sekund)..."):
            player_stats, team_stats = generate_advanced_stats(matches_df)

        if not player_stats.empty:
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("#### 🎯 Najlepsi strzelcy (gole i xG)")
                top_scorers = player_stats.sort_values(by='Gole', ascending=False).head(10)[['player', 'team', 'Gole', 'xG']]
                top_scorers['xG'] = top_scorers['xG'].round(2)
                top_scorers.columns = ['Zawodnik', 'Drużyna', 'Gole', 'xG']
                st.dataframe(top_scorers, use_container_width=True, hide_index=True)

                st.markdown("#### 🛡️ Interwencje obronne")
                top_def = player_stats.sort_values(by='Akcje Defensywne', ascending=False).head(10)[['player', 'team', 'Akcje Defensywne']]
                top_def['Akcje Defensywne'] = top_def['Akcje Defensywne'].astype(int)
                top_def.columns = ['Zawodnik', 'Drużyna', 'Odbiory / Przechwyty']
                st.dataframe(top_def, use_container_width=True, hide_index=True)

            with col_b:
                st.markdown("#### 🪄 Najlepsi kreatorzy")
                top_creators = player_stats.sort_values(by='Kluczowe Podania', ascending=False).head(10)[['player', 'team', 'Kluczowe Podania']]
                top_creators['Kluczowe Podania'] = top_creators['Kluczowe Podania'].astype(int)
                top_creators.columns = ['Zawodnik', 'Drużyna', 'Kluczowe Podania']
                st.dataframe(top_creators, use_container_width=True, hide_index=True)

                if not team_stats.empty:
                    st.markdown("#### ⚽ Jakość ofensywy (xG na Mecz)")
                    team_stats['xG / mecz'] = team_stats['xG / mecz'].round(2)
                    st.dataframe(team_stats[['team', 'xG / mecz']].head(10).rename(columns={'team': 'Drużyna'}), use_container_width=True, hide_index=True)
        else:
            st.warning("Nie udało się wygenerować zaawansowanych statystyk dla tej ligi.")

    st.markdown("---")

    # ==========================================
    # 4. HISTORIA SPOTKAŃ
    # ==========================================
    st.markdown("### 📋 Ostatnie Spotkania")
    
    display_df = matches_df[['match_date', 'home_team', 'home_score', 'away_score', 'away_team', 'competition_stage']].copy()
    display_df.columns = ['Data', 'Gospodarz', 'Gole Gosp.', 'Gole Gości', 'Gość', 'Faza/Kolejka']
    display_df = display_df.sort_values(by='Data', ascending=False).head(15) # Pokazujemy 15 najnowszych
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)