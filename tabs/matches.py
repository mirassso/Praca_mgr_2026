import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import data_loader as dl
import numpy as np
import base64

def get_base64_image(file_path):
    try:
        with open(file_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return f"data:image/svg+xml;base64,{encoded_string}"
    except FileNotFoundError:
        return None

def render(matches_df):
    st.title("⚽ Analiza zdarzeń meczowych")
    st.markdown("---")

    if matches_df.empty:
        st.warning("Brak meczów do analizy. Wybierz inną ligę z panelu bocznego.")
        return

    # Słownik ikon - wykorzystywany TYLKO do wizualizacji światła bramki
    outcome_icons = {
        'Saved': 'data/img/save.svg',
        'Saved to Post': 'data/img/save_to_post.svg',
        'Saved Off Target': 'data/img/save_off_t.svg',
        'Blocked': 'data/img/block.svg',
        'Off T': 'data/img/miss.svg',
        'Wayward': 'data/img/miss.svg'
    }

    matches_df = matches_df.copy()
    matches_df['match_label'] = matches_df['match_date'].astype(str) + " | " + matches_df['home_team'] + " vs " + matches_df['away_team']
    
    selected_match_label = st.selectbox("🔎 Wybierz mecz z listy:", matches_df['match_label'].unique())

    match_row = matches_df[matches_df['match_label'] == selected_match_label].iloc[0]
    match_id = match_row['match_id']
    home_team = match_row['home_team']
    away_team = match_row['away_team']

    with st.spinner("Pobieranie logów przestrzennych ze StatsBomb API..."):
        events_df = dl.get_match_events(match_id)

    if events_df.empty or 'type' not in events_df.columns:
        st.error("Nie udało się pobrać szczegółowych zdarzeń dla tego meczu.")
        return

    shots = events_df[events_df['type'] == 'Shot'].copy()

    if shots.empty:
        st.info("Brak zarejestrowanych strzałów w tym meczu.")
        return

    # KALIBRACJA GŁÓWNEGO BOISKA (Czyste UI)
    PITCH_LEFT_LINE = -15.0   
    PITCH_RIGHT_LINE = 115.0  
    PITCH_BOTTOM_LINE = 6.0   
    PITCH_TOP_LINE = 96.0     

    pitch_display_width = PITCH_RIGHT_LINE - PITCH_LEFT_LINE
    pitch_display_height = PITCH_TOP_LINE - PITCH_BOTTOM_LINE

    shots['scaled_x'] = PITCH_LEFT_LINE + ((shots['location_y'] / 80.0) * pitch_display_width)
    shots['scaled_y'] = PITCH_BOTTOM_LINE + ((shots['location_x'] / 120.0) * pitch_display_height)

    col_left, col_right = st.columns([4, 3])

    with col_left:
        st.markdown("### 📋 Rejestr strzałów")
        
        shots_display = shots[['minute', 'team', 'player', 'shot_outcome', 'shot_statsbomb_xg']].copy()
        shots_display = shots_display.sort_values(by='minute')
        shots_display.columns = ['Minuta', 'Drużyna', 'Zawodnik', 'Wynik', 'xG (StatsBomb)']
        
        team_filter = st.radio("Filtruj statystyki:", ["Wszyscy", home_team, away_team], horizontal=True)
        if team_filter != "Wszyscy":
            shots_display = shots_display[shots_display['Drużyna'] == team_filter]

        st.dataframe(shots_display, use_container_width=True, hide_index=True, height=400)

    # =========================================================================
    # 🗺️ GŁÓWNA MAPA BOISKA (Czysta, techniczna wizualizacja)
    # =========================================================================
    with col_right:
        st.markdown("### 🗺️ Mapa strzałów")
        
        fig = go.Figure()

        encoded_pitch = get_base64_image("data/img/pitch.svg")
        if encoded_pitch:
            fig.add_layout_image(dict(
                source=encoded_pitch, xref="x", yref="y",
                x=0, y=100, sizex=100, sizey=100,
                sizing="stretch", opacity=0.9, layer="below"
            ))

        map_shots = shots.copy()
        if team_filter != "Wszyscy":
            map_shots = map_shots[map_shots['team'] == team_filter]

        goals = map_shots[map_shots['shot_outcome'] == 'Goal']
        no_goals = map_shots[map_shots['shot_outcome'] != 'Goal']

        if not no_goals.empty:
            fig.add_trace(go.Scatter(
                x=no_goals['scaled_x'], y=no_goals['scaled_y'],
                mode='markers', name='Brak gola',
                marker=dict(size=10, color='#e74c3c', symbol='x', opacity=0.8),
                text=no_goals['player'] + "<br>Wynik: " + no_goals['shot_outcome'] + "<br>xG: " + no_goals['shot_statsbomb_xg'].round(2).astype(str),
                hoverinfo='text'
            ))

        if not goals.empty:
            fig.add_trace(go.Scatter(
                x=goals['scaled_x'], y=goals['scaled_y'],
                mode='markers', name='Gol',
                marker=dict(size=14, color='#2ecc71', symbol='circle', line=dict(width=2, color='white')),
                text=goals['player'] + "<br>Wynik: Goal<br>xG: " + goals['shot_statsbomb_xg'].round(2).astype(str),
                hoverinfo='text'
            ))

        fig.update_layout(
            xaxis=dict(range=[0, 100], visible=False), yaxis=dict(range=[0, 100], visible=False),
            margin=dict(l=10, r=10, t=10, b=10), 
            height=750, 
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # =========================================================================
    # 🥅 WIZUALIZACJA ŚWIATŁA BRAMKI (Z TWOJĄ GRAFIKĄ WEKTOROWĄ)
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🥅 Precyzyjna Lokalizacja Strzału (Światło Bramki)")

    shots['end_y'] = shots['shot_end_location'].apply(lambda loc: loc[1] if isinstance(loc, list) and len(loc) > 1 else np.nan)
    shots['end_z'] = shots['shot_end_location'].apply(lambda loc: loc[2] if isinstance(loc, list) and len(loc) > 2 else 0.0)

    valid_goal_shots = shots.dropna(subset=['end_y']).copy()

    if not valid_goal_shots.empty:
        valid_goal_shots = valid_goal_shots.sort_values(by='minute')
        if team_filter != "Wszyscy":
            valid_goal_shots = valid_goal_shots[valid_goal_shots['team'] == team_filter]

        if valid_goal_shots.empty:
            st.info(f"Wybrana drużyna ({team_filter}) nie oddała strzałów z trajektorią końcową.")
            return

        valid_goal_shots['shot_label'] = valid_goal_shots['minute'].astype(str) + "' | " + valid_goal_shots['player'] + " (" + valid_goal_shots['shot_outcome'] + ")"

        col_goal_list, col_goal_canvas = st.columns([5, 3])

        with col_goal_list:
            selected_goal_shot = st.selectbox("🎯 Wybierz strzał z listy:", valid_goal_shots['shot_label'])
            shot_detail = valid_goal_shots[valid_goal_shots['shot_label'] == selected_goal_shot].iloc[0]
            
            # --- Wyciąganie i tłumaczenie dodatkowych parametrów z danych StatsBomb ---
            body_part = shot_detail.get('shot_body_part', 'Brak danych')
            shot_type = shot_detail.get('shot_type', 'Brak danych')
            play_pattern = shot_detail.get('play_pattern', 'Brak danych')
            
            body_part_pl = {
                'Right Foot': 'Prawa noga', 'Left Foot': 'Lewa noga', 
                'Head': 'Głowa', 'Other': 'Inna część ciała'
            }.get(body_part, body_part)
            
            # Określanie kontekstu akcji (karny, wolny czy akcja)
            if shot_type == 'Penalty':
                shot_context = "Rzut karny"
            elif shot_type == 'Free Kick':
                shot_context = "Rzut wolny (bezpośredni)"
            else:
                shot_context = {
                    'Regular Play': 'Z gry', 
                    'From Corner': 'Rozegranie rzutu rożnego',
                    'From Free Kick': 'Rozegranie rzutu wolnego', 
                    'From Throw In': 'Rozegranie autu',
                    'From Counter': 'Kontratak', 
                    'From Goal Kick': 'Po wznowieniu od bramki',
                    'From Keeper': 'Od bramkarza',
                    'Other': 'Inne'
                }.get(play_pattern, play_pattern)
            # -------------------------------------------------------------------------
            
            st.markdown(f"**Szczegóły wykonania:**")
            st.markdown(f"- **Zawodnik:** {shot_detail['player']} ({shot_detail['team']})")
            st.markdown(f"- **Kontekst:** `{shot_context}` | **Wykonanie:** `{body_part_pl}`")
            st.markdown(f"- **Wynik akcji:** `{shot_detail['shot_outcome']}`")
            st.markdown(f"- **Trudność (StatsBomb xG):** `{shot_detail['shot_statsbomb_xg']:.2f}`")

        with col_goal_canvas:
            raw_y = shot_detail['end_y']
            raw_z = shot_detail['end_z']
            outcome = shot_detail['shot_outcome']

            # KALIBRACJA GEOMETRYCZNA(Canvas: 600x350px)
            G_LEFT = 14.17   
            G_RIGHT = 85.83  
            G_BOTTOM = 14.29  
            G_TOP = 62.86   
            
            g_width = G_RIGHT - G_LEFT
            g_height = G_TOP - G_BOTTOM

            goal_x = G_LEFT + ((raw_y - 36.0) / 8.0) * g_width
            goal_y = G_BOTTOM + ((raw_z - 0.0) / 2.67) * g_height

            # DYNAMICZNA KLATKA BEZPIECZEŃSTWA (Smart Clamping)
            clamped_x = max(2.5, min(goal_x, 97.5))
            clamped_y = max(2.0, min(goal_y, 97.5)) 

            fig_goal = go.Figure()

            encoded_goal = get_base64_image("data/img/goal.svg")
            if encoded_goal:
                fig_goal.add_layout_image(dict(
                    source=encoded_goal, xref="x", yref="y",
                    x=0, y=100, sizex=100, sizey=100, sizing="stretch", opacity=1.0, layer="below"
                ))

            specific_icon_path = outcome_icons.get(outcome)
            
            if specific_icon_path:
                encoded_specific_icon = get_base64_image(specific_icon_path)
                if encoded_specific_icon:
                    fig_goal.add_layout_image(dict(
                        source=encoded_specific_icon, xref="x", yref="y",
                        x=clamped_x, y=clamped_y, sizex=18, sizey=18, xanchor="center", yanchor="middle",
                        layer="above", sizing="contain"
                    ))
                
                fig_goal.add_trace(go.Scatter(
                    x=[clamped_x], y=[clamped_y], mode='markers', marker=dict(size=30, opacity=0),
                    hoverinfo='text', hovertext=f"Wysokość: {raw_z:.2f} jarda<br>Pozycja na linii: {raw_y:.2f}", showlegend=False
                ))
            else:
                color_marker = '#2ecc71' if outcome == 'Goal' else '#f39c12'
                fig_goal.add_trace(go.Scatter(
                    x=[clamped_x], y=[clamped_y], mode='markers',
                    marker=dict(size=14, color=color_marker, line=dict(color='white', width=2.0), symbol='circle'),
                    hoverinfo='text', hovertext=f"Wysokość: {raw_z:.2f} jarda<br>Pozycja na linii: {raw_y:.2f}", showlegend=False
                ))

            fig_goal.update_layout(
                xaxis=dict(range=[0, 100], visible=False), yaxis=dict(range=[0, 100], visible=False),
                margin=dict(l=0, r=0, t=0, b=0), height=250, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_goal, use_container_width=True)
    else:
        st.info("Brak strzałów z zarejestrowaną pozycją końcową dla tego meczu.")