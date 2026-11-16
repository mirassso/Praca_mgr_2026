import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import data_loader as dl
import base64
from scipy.stats import percentileofscore

def get_base64_image(file_path):
    try:
        with open(file_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return f"data:image/svg+xml;base64,{encoded_string}"
    except FileNotFoundError:
        return None

# --- POMOCNICZE FUNKCJE ---

@st.cache_data(show_spinner=False)
def build_player_database(matches_df):
    """
    Pobiera zdarzenia ze wszystkich meczów i buduje bazę statystyk graczy p90.
    """
    all_events = []
    
    # Pobieramy zdarzenia dla każdego meczu
    for match_id in matches_df['match_id']:
        events = dl.get_match_events(match_id)
        if not events.empty:
            all_events.append(events)
            
    if not all_events:
        return pd.DataFrame(), pd.DataFrame()
        
    full_df = pd.concat(all_events, ignore_index=True)
    
    # --- 1. OBLICZANIE MINUT I FILTROWANIE (+400 min) ---
    player_match_mins = full_df.groupby(['match_id', 'player'])['minute'].max().reset_index()
    total_minutes = player_match_mins.groupby('player')['minute'].sum().reset_index()
    total_minutes.rename(columns={'minute': 'minutes_played'}, inplace=True)
    
    # Odfiltrowanie zawodników poniżej 400 rozegranych minut
    total_minutes = total_minutes[total_minutes['minutes_played'] >= 400]
    
    if total_minutes.empty:
        return full_df, pd.DataFrame()
        
    valid_players = total_minutes['player'].tolist()
    filtered_df = full_df[full_df['player'].isin(valid_players)].copy()

    # --- 2. KATEGORYZACJA POZYCJI ---
    def map_position(pos):
        if pd.isna(pos): return 'Nieznana'
        pos = str(pos)
        if 'Back' in pos or 'Defender' in pos: return 'Obrońca'
        if 'Midfield' in pos: return 'Pomocnik'
        if 'Forward' in pos or 'Wing' in pos or 'Striker' in pos: return 'Napastnik'
        if 'Goalkeeper' in pos: return 'Bramkarz'
        return 'Inna'

    if 'position' in filtered_df.columns:
        filtered_df['broad_position'] = filtered_df['position'].apply(map_position)
        player_positions = filtered_df.groupby('player')['broad_position'].agg(lambda x: x.mode()[0] if not x.empty else 'Nieznana').reset_index()
    else:
        player_positions = pd.DataFrame({'player': filtered_df['player'].dropna().unique(), 'broad_position': 'Nieznana'})

    # --- 3. OBLICZANIE SUROWYCH STATYSTYK ---
    stats = []
    for player, group in filtered_df.groupby('player'):
        def_actions = len(group[group['type'].isin(['Interception', 'Block', 'Clearance', 'Duel'])])
        creativity = len(group[(group['type'] == 'Pass') & (group.get('pass_shot_assist') == True)])
        passes = len(group[group['type'] == 'Pass'])
        shots = len(group[group['type'] == 'Shot'])
        carries = len(group[group['type'] == 'Carry'])
        pressures = len(group[group['type'] == 'Pressure'])
        
        mins = total_minutes[total_minutes['player'] == player]['minutes_played'].values[0]

        stats.append({
            'player': player,
            'minutes_played': mins,
            'Akcje Defensywne': def_actions,
            'Kreatywność': creativity,
            'Rozegranie': passes,
            'Strzały': shots,
            'Prowadzenie Piłki': carries,
            'Presja': pressures
        })
        
    stats_df = pd.DataFrame(stats)
    stats_df = stats_df.merge(player_positions, on='player', how='left')
    
    # --- 4. PRZELICZANIE NA P90 I PERCENTYLE ---
    metrics = ['Akcje Defensywne', 'Kreatywność', 'Rozegranie', 'Strzały', 'Prowadzenie Piłki', 'Presja']
    for metric in metrics:
        stats_df[f'{metric}_p90'] = (stats_df[metric] / stats_df['minutes_played']) * 90.0
        stats_df[f'{metric}_pct'] = stats_df.groupby('broad_position')[f'{metric}_p90'].rank(pct=True) * 100
        stats_df[f'{metric}_pct'] = stats_df[f'{metric}_pct'].fillna(0).round(0)

    return full_df, stats_df

# --- GŁÓWNA FUNKCJA RENDERUJĄCA ---

def render(matches_df):
    st.title("🏃 Analiza zawodników")
    st.markdown("---")

    if matches_df.empty:
        st.warning("Brak meczów w wybranych rozgrywkach.")
        return
        
    # Słownik ikon do mapowania wyników strzałów
    outcome_icons = {
        'Saved': 'data/img/save.svg',
        'Saved to Post': 'data/img/save_to_post.svg',
        'Saved Off Target': 'data/img/save_off_t.svg',
        'Blocked': 'data/img/block.svg',
        'Off T': 'data/img/miss.svg',
        'Wayward': 'data/img/miss.svg'
    }

    # 1. Budowanie bazy danych w tle
    with st.spinner("Budowanie bazy skautingowej dla całej ligi (to może potrwać kilkanaście sekund)..."):
        full_events_df, player_stats_df = build_player_database(matches_df)

    if player_stats_df.empty:
        st.error("Nie udało się zbudować bazy zawodników. Upewnij się, że rozegrano wystarczająco dużo minut (filtr >400 min).")
        return

    player_stats_df = player_stats_df.dropna(subset=['player'])
    all_players = sorted(player_stats_df['player'].unique().tolist())

    # 2. Filtr główny: Wybór Zawodnika
    selected_player = st.selectbox("👤 Wybierz zawodnika do analizy:", all_players)
    
    player_data = player_stats_df[player_stats_df['player'] == selected_player].iloc[0]
    player_position = player_data['broad_position']

    st.markdown(f"### Wykres radarowy: **{selected_player}** (pozycja: {player_position})")
    
    # SEKCJA 1: STATYSTYKI OGÓLNE (RADAR)
    col1, col2 = st.columns([1, 1])
    with col1:
        # Słownik do poprawnej gramatycznie odmiany pozycji (kogo? czego?)
        odmiana_pozycji = {
            'Obrońca': 'obrońców',
            'Pomocnik': 'pomocników',
            'Napastnik': 'napastników',
            'Bramkarz': 'bramkarzy',
            'Nieznana': 'zawodników'
        }
        pozycja_odmieniona = odmiana_pozycji.get(player_position, 'zawodników')
        
        st.info(f"Poniższy wykres prezentuje percentyle. Wartość 90 oznacza, że zawodnik jest lepszy niż 90% **{pozycja_odmieniona}** w wybranej lidze (statystyki przeliczone na 90 min, uwzględniając wyłącznie graczy z minimum 400 rozegranymi minutami w bazie).")
        
        categories = ['Akcje Defensywne', 'Kreatywność', 'Rozegranie', 'Strzały', 'Prowadzenie Piłki', 'Presja']
        values = [player_data[f'{cat}_pct'] for cat in categories]
        
        # Zamykamy obrys radaru
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_closed, 
            theta=categories_closed, 
            fill='toself', 
            name=selected_player,
            line=dict(color='#2ecc71', width=2), 
            fillcolor='rgba(46, 204, 113, 0.4)',
            marker=dict(color='#27ae60', size=8)
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255, 255, 255, 0.1)', linecolor='rgba(255, 255, 255, 0.2)'),
                angularaxis=dict(gridcolor='rgba(255, 255, 255, 0.1)', linecolor='rgba(255, 255, 255, 0.2)'),
                bgcolor='rgba(0,0,0,0)'
            ), 
            showlegend=False, 
            height=450, 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(color='white')
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.markdown("#### Wartości p90 (Na 90 minut)")
        st.markdown(f"*Rozegrane minuty w sezonie: **{int(player_data['minutes_played'])}***")
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Odbiory, Bloki, Przechwyty", f"{player_data['Akcje Defensywne_p90']:.2f}")
            st.metric("Podania Kluczowe", f"{player_data['Kreatywność_p90']:.2f}")
            st.metric("Prowadzenie Piłki", f"{player_data['Prowadzenie Piłki_p90']:.2f}")
        with m_col2:
            st.metric("Rozegranie (Podania)", f"{player_data['Rozegranie_p90']:.2f}")
            st.metric("Strzały", f"{player_data['Strzały_p90']:.2f}")
            st.metric("Skoki Pressingowe", f"{player_data['Presja_p90']:.2f}")

    st.markdown("---")
    
    # SEKCJA 2: ANALIZA MECZU (MAPA PODAŃ I STRZAŁÓW)
    st.markdown("### 🔍 Analiza szczegółowa z wybranego spotkania")
    
    player_events = full_events_df[full_events_df['player'] == selected_player]
    played_match_ids = player_events['match_id'].unique()
    played_matches_df = matches_df[matches_df['match_id'].isin(played_match_ids)].copy()
    played_matches_df['match_label'] = played_matches_df['match_date'].astype(str) + " | " + played_matches_df['home_team'] + " vs " + played_matches_df['away_team']
    
    if played_matches_df.empty:
        st.warning("Brak szczegółowych danych z meczów dla tego gracza.")
        return
        
    selected_match_label = st.selectbox("🏟️ Wybierz mecz do głębokiej analizy:", played_matches_df['match_label'])
    selected_match_id = played_matches_df[played_matches_df['match_label'] == selected_match_label].iloc[0]['match_id']
    
    # KALIBRACJA BOISKA
    P_LEFT = 1.0
    P_RIGHT = 99.0
    P_BOTT = 1.0
    P_TOP = 99.0
    
    p_width = P_RIGHT - P_LEFT
    p_height = P_TOP - P_BOTT

    # ==========================================
    # 🗺️ 1. MAPA PODAŃ
    # ==========================================
    st.markdown("#### 1. Dystrybucja podań")
    
    # CSS WYMUSZAJĄCY BŁĘKITNE CHECKBOXY W STREAMLIT
    st.markdown("""
    <style>
    div[data-testid="stCheckbox"] label span[data-baseweb="checkbox"] div[data-checked="true"] {
        background-color: #3498db !important;
        border-color: #3498db !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    match_passes = player_events[(player_events['match_id'] == selected_match_id) & (player_events['type'] == 'Pass')].copy()
    
    if match_passes.empty:
        st.info("Brak podań tego zawodnika w wybranym meczu.")
    else:
        match_passes['start_x_scaled'] = P_LEFT + ((match_passes['location_y'] / 80.0) * p_width)
        match_passes['start_y_scaled'] = P_BOTT + ((match_passes['location_x'] / 120.0) * p_height)
        match_passes['end_x_scaled'] = P_LEFT + ((match_passes['pass_end_y'] / 80.0) * p_width)
        match_passes['end_y_scaled'] = P_BOTT + ((match_passes['pass_end_x'] / 120.0) * p_height)

        col_left_desc, col_right_map = st.columns(2)

        with col_left_desc:
            st.markdown(f"**Filtruj rodzaj podań na wykresie:**")
            show_prog = st.checkbox("🔵 Progresywne podania", value=True)
            show_succ = st.checkbox("🟢 Celne podania", value=True)
            show_fail = st.checkbox("🔴 Niecelne podania", value=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            all_p = len(match_passes)
            failed_p = len(match_passes[match_passes['pass_outcome'].notna()])
            succ_p = all_p - failed_p
            perc = (succ_p / all_p * 100) if all_p > 0 else 0
            
            if all_p > 0:
                dist_start = np.sqrt((120 - match_passes['location_x'])**2 + (40 - match_passes['location_y'])**2)
                dist_end = np.sqrt((120 - match_passes['pass_end_x'])**2 + (40 - match_passes['pass_end_y'])**2)
                match_passes['is_progressive'] = (match_passes['pass_outcome'].isna()) & ((dist_start - dist_end) >= 10.0)
                prog_p = int(match_passes['is_progressive'].sum())
            else:
                match_passes['is_progressive'] = False
                prog_p = 0
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Liczba podań", all_p)
                st.metric("Celne podania", succ_p)
            with metric_col2:
                st.metric("Celność podań", f"{perc:.0f}%")
                st.metric("Podania progresywne", prog_p)

        with col_right_map:
            fig_pass = go.Figure()
            
            encoded_pitch = get_base64_image("data/img/pitch.svg")
            if encoded_pitch:
                fig_pass.add_layout_image(
                    dict(source=encoded_pitch, xref="x", yref="y", x=0, y=100, sizex=100, sizey=100, sizing="stretch", opacity=0.9, layer="below")
                )

            failed_passes = match_passes[match_passes['pass_outcome'].notna()]
            prog_passes = match_passes[match_passes['is_progressive'] == True]
            successful_passes = match_passes[(match_passes['pass_outcome'].isna()) & (match_passes['is_progressive'] == False)]

            if show_succ and not successful_passes.empty:
                for _, row in successful_passes.iterrows():
                    fig_pass.add_annotation(
                        x=row['end_x_scaled'], y=row['end_y_scaled'],
                        ax=row['start_x_scaled'], ay=row['start_y_scaled'],
                        xref='x', yref='y', axref='x', ayref='y',
                        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='rgba(46, 204, 113, 0.7)'
                    )
                fig_pass.add_trace(go.Scatter(
                    x=successful_passes['start_x_scaled'], y=successful_passes['start_y_scaled'], 
                    mode='markers', marker=dict(size=9, color='#2ecc71'), hoverinfo='none', showlegend=False
                ))

            if show_prog and not prog_passes.empty:
                for _, row in prog_passes.iterrows():
                    fig_pass.add_annotation(
                        x=row['end_x_scaled'], y=row['end_y_scaled'],
                        ax=row['start_x_scaled'], ay=row['start_y_scaled'],
                        xref='x', yref='y', axref='x', ayref='y',
                        showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=3, arrowcolor='rgba(52, 152, 219, 0.9)'
                    )
                fig_pass.add_trace(go.Scatter(
                    x=prog_passes['start_x_scaled'], y=prog_passes['start_y_scaled'], 
                    mode='markers', marker=dict(size=9, color='#3498db', line=dict(width=1, color='white')), hoverinfo='none', showlegend=False
                ))

            if show_fail and not failed_passes.empty:
                for _, row in failed_passes.iterrows():
                    fig_pass.add_annotation(
                        x=row['end_x_scaled'], y=row['end_y_scaled'],
                        ax=row['start_x_scaled'], ay=row['start_y_scaled'],
                        xref='x', yref='y', axref='x', ayref='y',
                        showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=2, arrowcolor='rgba(231, 76, 60, 0.7)'
                    )
                fig_pass.add_trace(go.Scatter(
                    x=failed_passes['start_x_scaled'], y=failed_passes['start_y_scaled'], 
                    mode='markers', marker=dict(size=9, color='#e74c3c'), hoverinfo='none', showlegend=False
                ))

            fig_pass.update_layout(
                xaxis=dict(range=[0, 100], visible=False), 
                yaxis=dict(range=[0, 100], visible=False, scaleanchor="x", scaleratio=1.5),
                margin=dict(l=10, r=10, t=10, b=10), height=600,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pass, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 🎯 2. ANALIZA STRZAŁÓW (W JEDNYM RZĘDZIE)
    # ==========================================
    st.markdown("#### 2. Aktywność strzelecka")
    
    match_shots = player_events[(player_events['match_id'] == selected_match_id) & (player_events['type'] == 'Shot')].copy()

    if match_shots.empty:
        st.info("Brak oddanych strzałów w wybranym meczu.")
    else:
        # Podział na równe kolumny, by mapa strzałów i bramka były obok siebie
        col_shot_map, col_shot_goal = st.columns(2)

        with col_shot_map:
            st.markdown("<h5 style='text-align:center;'>Mapa Strzałów</h1>", unsafe_allow_html=True)
            
            # Mapowanie osi dla rzutu boiska (tak samo jak przy podaniach)
            match_shots['start_x_scaled'] = P_LEFT + ((match_shots['location_y'] / 80.0) * p_width)
            match_shots['start_y_scaled'] = P_BOTT + ((match_shots['location_x'] / 120.0) * p_height)
            
            fig_shots = go.Figure()
            
            encoded_pitch_shot = get_base64_image("data/img/pitch.svg")
            if encoded_pitch_shot:
                fig_shots.add_layout_image(
                    dict(source=encoded_pitch_shot, xref="x", yref="y", x=0, y=100, sizex=100, sizey=100, sizing="stretch", opacity=0.9, layer="below")
                )

            goals = match_shots[match_shots['shot_outcome'] == 'Goal']
            no_goals = match_shots[match_shots['shot_outcome'] != 'Goal']

            if not no_goals.empty:
                fig_shots.add_trace(go.Scatter(
                    x=no_goals['start_x_scaled'], y=no_goals['start_y_scaled'],
                    mode='markers', name='Brak gola',
                    marker=dict(size=12, color='#e74c3c', symbol='x', opacity=0.8),
                    text="Wynik: " + no_goals['shot_outcome'] + "<br>xG: " + no_goals['shot_statsbomb_xg'].round(2).astype(str),
                    hoverinfo='text'
                ))

            if not goals.empty:
                fig_shots.add_trace(go.Scatter(
                    x=goals['start_x_scaled'], y=goals['start_y_scaled'],
                    mode='markers', name='Gol',
                    marker=dict(size=16, color='#2ecc71', symbol='circle', line=dict(width=2, color='white')),
                    text="Wynik: Goal<br>xG: " + goals['shot_statsbomb_xg'].round(2).astype(str),
                    hoverinfo='text'
                ))

            fig_shots.update_layout(
                xaxis=dict(range=[0, 100], visible=False), 
                yaxis=dict(range=[0, 100], visible=False, scaleanchor="x", scaleratio=1.5), # WYMUSZENIE PROPORCJI
                margin=dict(l=10, r=10, t=10, b=10), height=600, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_shots, use_container_width=True)

        with col_shot_goal:
            st.markdown("<h5 style='text-align:center;'>Celność i Wykonanie</h1>", unsafe_allow_html=True)
            
            match_shots['end_y'] = match_shots['shot_end_location'].apply(lambda loc: loc[1] if isinstance(loc, list) and len(loc) > 1 else np.nan)
            match_shots['end_z'] = match_shots['shot_end_location'].apply(lambda loc: loc[2] if isinstance(loc, list) and len(loc) > 2 else 0.0)

            valid_goal_shots = match_shots.dropna(subset=['end_y']).copy()

            if valid_goal_shots.empty:
                st.info("Brak zarejestrowanej trajektorii końcowej strzałów (np. zablokowane natychmiast po uderzeniu).")
            else:
                valid_goal_shots = valid_goal_shots.sort_values(by='minute')
                valid_goal_shots['shot_label'] = valid_goal_shots['minute'].astype(str) + "' | " + valid_goal_shots['shot_outcome']

                selected_goal_shot = st.selectbox("🎯 Wybierz strzał:", valid_goal_shots['shot_label'])
                shot_detail = valid_goal_shots[valid_goal_shots['shot_label'] == selected_goal_shot].iloc[0]
                
                # --- Wyciąganie i tłumaczenie dodatkowych parametrów ---
                body_part = shot_detail.get('shot_body_part', 'Brak danych')
                shot_type = shot_detail.get('shot_type', 'Brak danych')
                play_pattern = shot_detail.get('play_pattern', 'Brak danych')
                
                body_part_pl = {
                    'Right Foot': 'Prawa noga', 'Left Foot': 'Lewa noga', 
                    'Head': 'Głowa', 'Other': 'Inna część ciała'
                }.get(body_part, body_part)
                
                if shot_type == 'Penalty':
                    shot_context = "Rzut karny"
                elif shot_type == 'Free Kick':
                    shot_context = "Rzut wolny"
                else:
                    shot_context = {
                        'Regular Play': 'Z gry', 
                        'From Corner': 'Po rzucie rożnym',
                        'From Free Kick': 'Rozegranie rzutu wolnego', 
                        'From Throw In': 'Rozegranie autu',
                        'From Counter': 'Kontratak', 
                        'From Goal Kick': 'Po wznowieniu od bramki',
                        'From Keeper': 'Od bramkarza',
                        'Other': 'Inne'
                    }.get(play_pattern, play_pattern)
                
                # Zwięzły opis strzału
                st.markdown(f"""
                <div style='background-color:rgba(255,255,255,0.05); padding:10px; border-radius:10px; margin-bottom:15px; font-size:0.95em'>
                    <strong>Akcja:</strong> <span style='color:#3498db'>{shot_context}</span><br>
                    <strong>Wykonanie:</strong> <span style='color:#e67e22'>{body_part_pl}</span><br>
                    <strong>xG:</strong> <span>{shot_detail['shot_statsbomb_xg']:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
                
                raw_y = shot_detail['end_y']
                raw_z = shot_detail['end_z']
                outcome = shot_detail['shot_outcome']

                # ==========================================
                # 📐 PIXEL-PERFECT GEOMETRIC CALIBRATION
                # ==========================================
                G_LEFT = 14.17   
                G_RIGHT = 85.83  
                G_BOTTOM = 14.29  
                G_TOP = 62.86   
                
                g_width = G_RIGHT - G_LEFT
                g_height = G_TOP - G_BOTTOM

                goal_x = G_LEFT + ((raw_y - 36.0) / 8.0) * g_width
                goal_y = G_BOTTOM + ((raw_z - 0.0) / 2.67) * g_height

                # Klatka bezpieczeństwa zapobiegająca wyjechaniu ikony poza wykres
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
                    margin=dict(l=0, r=0, t=0, b=0), height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_goal, use_container_width=True)