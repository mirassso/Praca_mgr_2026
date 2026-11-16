import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import data_loader as dl

def render(matches_df):
    st.title("🎯 Przewidywane Gole i Przebieg Spotkania")
    st.markdown("---")

    # 1. Interfejs wyboru meczu
    matches_df = matches_df.copy().sort_values(by='match_date', ascending=True)
    matches_df['match_label'] = matches_df['match_date'].astype(str) + " | " + matches_df['home_team'] + " vs " + matches_df['away_team']
    selected_match_label = st.selectbox("🔎 Wybierz mecz do analizy xG i Momentum:", matches_df['match_label'].unique())

    match_row = matches_df[matches_df['match_label'] == selected_match_label].iloc[0]
    match_id = match_row['match_id']
    home_team = match_row['home_team']
    away_team = match_row['away_team']

    # 2. Pobieranie danych i ekstrakcja strzałów
    with st.spinner("Przetwarzanie zdarzeń i strzałów przez modele analityczne..."):
        events_df = dl.get_match_events(match_id)
        
    if events_df.empty or 'type' not in events_df.columns:
        st.warning("Brak danych zdarzeniowych dla tego meczu.")
        return
        
    # ODDZIELENIE GRY OD RZUTÓW KARNYCH
    match_events = events_df[events_df['period'] <= 4].copy() # Gra z gry i dogrywka
    shootout_events = events_df[events_df['period'] == 5].copy() # Seria rzutów karnych
        
    # Pobieramy dynamicznie maksymalną minutę z samej gry, aby osie X były dokładne!
    if not match_events.empty:
        max_minute = match_events['minute'].max() + 1
    else:
        max_minute = 90

    # Analizujemy strzały tylko z samej gry!
    shots = match_events[match_events['type'] == 'Shot'].copy()
    
    if shots.empty:
        st.info("Brak strzałów w tym meczu.")
        return

    # Zabezpieczenie na wypadek braków w danych StatsBomb
    if 'shot_statsbomb_xg' not in shots.columns:
        shots['shot_statsbomb_xg'] = 0.0
    else:
        shots['shot_statsbomb_xg'] = shots['shot_statsbomb_xg'].fillna(0.0)

    # ==========================================
    # 📊 WIZUALIZACJA: Dashboard Przebiegu Meczu
    # ==========================================
    
    # OBSŁUGA INFORMACJI O SERII RZUTÓW KARNYCH
    if not shootout_events.empty:
        shootout_shots = shootout_events[shootout_events['type'] == 'Shot'].copy()
        
        home_penalties = len(shootout_shots[(shootout_shots['team'] == home_team) & (shootout_shots['shot_outcome'] == 'Goal')])
        away_penalties = len(shootout_shots[(shootout_shots['team'] == away_team) & (shootout_shots['shot_outcome'] == 'Goal')])
        
        st.info(
            f"🏆 **Mecz rozstrzygnął się w rzutach karnych!** "
            f"Wynik serii jedenastek: **{home_team} {home_penalties}:{away_penalties} {away_team}**"
        )
        st.markdown("---")
        
    st.markdown(f"### 📈 Przebieg meczu: **{home_team}** vs **{away_team}**")
    
    # Sortowanie po minucie
    shots = shots.sort_values(by='minute')

    # Sumy xG dla obu drużyn (StatsBomb)
    home_xg_total = shots[shots['team'] == home_team]['shot_statsbomb_xg'].sum()
    away_xg_total = shots[shots['team'] == away_team]['shot_statsbomb_xg'].sum()
    
    # Faktyczne gole
    home_goals = len(shots[(shots['team'] == home_team) & (shots['shot_outcome'] == 'Goal')])
    away_goals = len(shots[(shots['team'] == away_team) & (shots['shot_outcome'] == 'Goal')])

    # Wyświetlanie kafelków z wynikiem
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Gole ({home_team})", home_goals)
    col2.metric("Oczekiwane (xG)", f"{home_xg_total:.2f}")
    col3.metric(f"Gole ({away_team})", away_goals)
    col4.metric("Oczekiwane (xG)", f"{away_xg_total:.2f}")

    # ---------------------------------------------------------
    # WYKRES 1: SKUMULOWANE xG
    # ---------------------------------------------------------
    fig_xg = go.Figure()

    for team, color in zip([home_team, away_team], ['#3498db', '#e74c3c']):
        team_shots = shots[shots['team'] == team].copy()
        
        # Obliczanie skumulowanej sumy xG (StatsBomb)
        team_shots['cumulative_xG'] = team_shots['shot_statsbomb_xg'].cumsum()
        
        # Oś X dostosowana do dynamicznej długości meczu (max_minute)
        x_vals = [0] + team_shots['minute'].tolist() + [max_minute]
        y_vals = [0] + team_shots['cumulative_xG'].tolist() + [team_shots['cumulative_xG'].max() if not team_shots.empty else 0]

        # Wykres schodkowy (Step)
        fig_xg.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines',
            line_shape='hv', 
            name=team,
            line=dict(color=color, width=3),
            fill='tozeroy',
            fillcolor=color.replace(')', ', 0.1)').replace('#3498db', 'rgba(52, 152, 219, 0.1)').replace('#e74c3c', 'rgba(231, 76, 60, 0.1)')
        ))

        # Dodajemy punkty dla faktycznych goli (z gwiazdką)
        goals = team_shots[team_shots['shot_outcome'] == 'Goal']
        if not goals.empty:
            fig_xg.add_trace(go.Scatter(
                x=goals['minute'],
                y=goals['cumulative_xG'],
                mode='markers+text',
                name=f'Gole {team}',
                marker=dict(color=color, size=14, symbol='star', line=dict(width=2, color='white')),
                text=goals['player'],
                textposition="top center",
                showlegend=False
            ))

    fig_xg.update_layout(
        title="Skumulowane Expected Goals - xG (StatsBomb)",
        xaxis_title='Minuta spotkania',
        yaxis_title='Skumulowane xG',
        xaxis=dict(range=[0, max_minute]),
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig_xg.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333333')
    fig_xg.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333333')

    st.plotly_chart(fig_xg, use_container_width=True)

    # ---------------------------------------------------------
    # WYKRES 2: MATCH MOMENTUM (Inicjatywa i Dominacja)
    # ---------------------------------------------------------
    
    # 1. Zbieramy tylko konstruktywne akcje (oparte na match_events, bez karnych!)
    action_types = ['Pass', 'Carry', 'Shot']
    actions = match_events[match_events['type'].isin(action_types)].copy()

    # 2. Liczymy akcje per minuta per drużyna
    actions_per_min = actions.groupby(['minute', 'team']).size().reset_index(name='action_count')

    # 3. Pusta oś czasu
    timeline = pd.DataFrame({'minute': range(0, max_minute + 1)})

    # 4. Mergowanie danych obu drużyn
    home_actions = actions_per_min[actions_per_min['team'] == home_team][['minute', 'action_count']]
    timeline = timeline.merge(home_actions, on='minute', how='left').rename(columns={'action_count': 'home_actions'})
    
    away_actions = actions_per_min[actions_per_min['team'] == away_team][['minute', 'action_count']]
    timeline = timeline.merge(away_actions, on='minute', how='left').rename(columns={'action_count': 'away_actions'})

    timeline = timeline.fillna(0)

    # 5. Obliczenie Momentum (Różnica akcji)
    timeline['raw_momentum'] = timeline['home_actions'] - timeline['away_actions']

    # 6. Wygładzanie (Średnia krocząca, okno=5 minut)
    timeline['momentum_smoothed'] = timeline['raw_momentum'].rolling(window=5, min_periods=1).mean()

    timeline['home_momentum'] = np.where(timeline['momentum_smoothed'] > 0, timeline['momentum_smoothed'], 0)
    timeline['away_momentum'] = np.where(timeline['momentum_smoothed'] < 0, timeline['momentum_smoothed'], 0)

    # 7. Rysowanie wykresu Momentum
    fig_mom = go.Figure()

    # Przewaga Gospodarzy
    fig_mom.add_trace(go.Scatter(
        x=timeline['minute'], 
        y=timeline['home_momentum'],
        mode='lines',
        line=dict(width=0),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.7)', # Niebieski (Home)
        name=f"Przewaga: {home_team}",
        hoverinfo='none'
    ))

    # Przewaga Gości
    fig_mom.add_trace(go.Scatter(
        x=timeline['minute'], 
        y=timeline['away_momentum'],
        mode='lines',
        line=dict(width=0),
        fill='tozeroy',
        fillcolor='rgba(231, 76, 60, 0.7)', # Czerwony (Away)
        name=f"Przewaga: {away_team}",
        hoverinfo='none'
    ))

    fig_mom.add_hline(y=0, line_width=2, line_color="white", opacity=0.3)

    fig_mom.update_layout(
        title="Match Momentum - Inicjatywa i Dominacja",
        xaxis_title='Minuta spotkania',
        yaxis_title='Intensywność',
        xaxis=dict(range=[0, max_minute]), # Ta sama oś X co na xG!
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False), # Ukrywamy liczby na osi Y
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig_mom.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333333')

    st.plotly_chart(fig_mom, use_container_width=True)

    # ==========================================
    # 5. Tabela najlepszych strzałów
    # ==========================================
    st.markdown("---")
    st.markdown("### 🔥 Najgroźniejsze strzały w meczu")
    
    # Wyciąganie koordynatów tylko na potrzeby tabeli (dystans)
    shots['x'] = shots['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else np.nan)
    shots['y'] = shots['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else np.nan)
    shots['distance_to_goal'] = np.sqrt((120 - shots['x'])**2 + (40 - shots['y'])**2)
    
    top_shots = shots[['minute', 'team', 'player', 'shot_statsbomb_xg', 'shot_outcome', 'distance_to_goal']].copy()
    top_shots = top_shots.sort_values(by='shot_statsbomb_xg', ascending=False).head(10)
    top_shots['shot_statsbomb_xg'] = top_shots['shot_statsbomb_xg'].round(3)
    top_shots['distance_to_goal'] = top_shots['distance_to_goal'].round(1).astype(str) + " m"
    
    top_shots.columns = ['Minuta', 'Drużyna', 'Zawodnik', 'xG (StatsBomb)', 'Efekt', 'Dystans']
    st.dataframe(top_shots, use_container_width=True, hide_index=True)