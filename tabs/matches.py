import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import base64
import os
import joblib # NOWY IMPORT DO MODELU

# --- FUNKCJE POMOCNICZE ---

def clean_text(text):
    if not isinstance(text, str): return text
    try: text = text.encode('cp1252').decode('utf-8')
    except: pass
    mojibake_dict = {
        'A©': 'é', 'Ã©': 'é', 'A¨': 'è', 'Ã¨': 'è', 'A±': 'ñ', 'Ã±': 'ñ',
        'A³': 'ó', 'Ã³': 'ó', 'A¡': 'á', 'Ã¡': 'á', 'A-': 'í', 'Ã­': 'í',
        'A¼': 'ü', 'Ã¼': 'ü', 'A§': 'ç', 'Ã§': 'ç', 'Aº': 'ú', 'Ãº': 'ú',
        'A´': 'ô', 'Ã´': 'ô', 'A¶': 'ö', 'Ã¶': 'ö', 'A¤': 'ä', 'Ã¤': 'ä'
    }
    for bad, good in mojibake_dict.items(): text = text.replace(bad, good)
    return text

def get_base64_image(image_path):
    if not os.path.exists(image_path): return None
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
        return f"data:image/svg+xml;base64,{encoded}"

# --- FUNKCJA ŁADUJĄCA MODEL ML ---
# Używamy @st.cache_resource, aby model załadował się tylko raz, a nie przy każdym kliknięciu
@st.cache_resource
def load_xg_model():
    try:
        model = joblib.load('models/xg_model.joblib')
        cols = joblib.load('models/xg_columns.joblib')
        return model, cols
    except Exception as e:
        return None, None

# PITCH_MAP i GOAL_MAP (Skrócone dla czytelności kodu)
PITCH_MAP = {1: (50, 75), 2: (50, 25), 3: (50, 88), 4: (10, 75), 5: (90, 75), 6: (15, 60), 7: (20, 92), 8: (80, 92), 9: (30, 88), 10: (38, 95), 11: (70, 88), 12: (62, 95), 13: (50, 96), 14: (50, 89), 15: (50, 78), 16: (50, 65), 17: (50, 55), 18: (50, 45), 19: (50, 50)}
GOAL_MAP = {1: (50, 110), 2: (50, 50), 3: (15, 15), 4: (85, 15), 5: (50, 50), 6: (20, 120), 7: (50, 85), 8: (0, 50), 9: (100, 50), 10: (50, 130), 11: (50, 80), 12: (15, 80), 13: (85, 80)}


def render(events, ginf):
    st.title("⚽ Analiza meczów")

    # Ładujemy model i kolumny na starcie
    xg_model, xg_cols = load_xg_model()

    match_list = ginf.apply(lambda x: f"{x['ht']} vs {x['at']} ({x['season']})", axis=1)
    selected_match = st.selectbox("Wybierz mecz:", match_list)

    match_info = ginf[match_list == selected_match].iloc[0]
    match_id = match_info['id_odsp']
    home_team = match_info['ht']
    away_team = match_info['at']
    
    match_events = events[events['id_odsp'] == match_id].copy()

    # Relacja z meczu...
    st.write(f"### Relacja z meczu: {selected_match}")
    table_data = match_events[['time', 'event_team', 'event_type_name', 'text']].copy()
    table_data['text'] = table_data['text'].apply(clean_text)
    table_data = table_data.sort_values(by='time', ascending=True)

    st.dataframe(table_data, hide_index=True, use_container_width=True, height=250, 
                 column_config={"time": st.column_config.NumberColumn("Minuta", format="%d'"), "event_team": "Drużyna", "event_type_name": "Zdarzenie", "text": st.column_config.TextColumn("Opis sytuacji", width="large")})
    st.markdown("---")

    # --- WIZUALIZACJA: PODGLĄD ZDARZENIA (STRZAŁY) ---
    st.write("### 🔎 Podgląd Zdarzenia (Strzały)")
    shots_df = match_events[match_events['is_shot'] == True].copy()
    
    if not shots_df.empty:
        col_info, col_viz = st.columns([1, 0.4])
        
        with col_info:
            shot_labels = shots_df.apply(lambda x: f"{int(x['time'])}' - {x['event_team']}: {clean_text(str(x['text']))[:50]}...", axis=1)
            selected_shot_label = st.selectbox("Wybierz strzał do wizualizacji:", shot_labels)
            
            shot_idx = shot_labels[shot_labels == selected_shot_label].index[0]
            selected_shot = shots_df.loc[shot_idx]
            
            st.markdown("#### 📝 Pełny opis zdarzenia")
            st.info(clean_text(str(selected_shot['text'])))
            
            # --- SEKCJA PREDYKCJI xG ---
            if xg_model and xg_cols:
                # 1. Tworzymy pusty DataFrame z zerami o strukturze z Jupytera
                input_df = pd.DataFrame(0, index=[0], columns=xg_cols)
                
                # 2. Wypełniamy zmienną numeryczną
                if 'fast_break' in xg_cols:
                    input_df.at[0, 'fast_break'] = int(selected_shot.get('fast_break', 0))
                
                # 3. Wypełniamy zmienne kategoryczne (One-Hot Encoding w locie)
                for cat in ['location', 'bodypart', 'assist_method', 'situation']:
                    val = selected_shot.get(cat)
                    if pd.notna(val):
                        col_name = f"{cat}_{int(val)}" # Odwzorowanie pd.get_dummies (np. 'location_15')
                        if col_name in xg_cols:
                            input_df.at[0, col_name] = 1
                
                # 4. Przewidujemy prawdopodobieństwo (indeks 1 to gol)
                xg_value = xg_model.predict_proba(input_df)[0][1]
                
                # Wyświetlamy jako ładny Metric box
                col1, col2 = st.columns(2)
                col1.metric(label="📊 Model xG", value=f"{xg_value:.2f}")
                
                is_goal_text = "✅ Gol" if selected_shot.get('is_goal') == 1 else "❌ Pudło/Obrona"
                col2.metric(label="⚽ Rezultat", value=is_goal_text)
                
            else:
                st.warning("Nie znaleziono modelu xG w folderze 'data/'. Uruchom najpierw notatnik Jupyter.")
                st.write(f"**Zdobyto bramkę:** {'✅ Tak (Gol)' if selected_shot.get('is_goal') == 1 else '❌ Nie'}")

        with col_viz:
            pitch_b64 = get_base64_image("data/img/pitch.svg")
            goal_b64 = get_base64_image("data/img/goal.svg")
            
            icon_path = "data/img/miss.svg" 
            if selected_shot.get('is_goal') == 1:
                icon_path = "data/img/ball_g.svg"
            else:
                outcome = selected_shot.get('shot_outcome')
                text_lower = str(selected_shot.get('text', '')).lower()
                if outcome == 3 or 'saved' in text_lower or 'blocked' in text_lower:
                    icon_path = "data/img/ball.svg"
                    
            icon_b64 = get_base64_image(icon_path)

            st.markdown("#### 📍 Lokalizacja na murawie")
            fig_pitch = go.Figure()
            fig_pitch.update_layout(xaxis=dict(range=[0, 100], visible=False), yaxis=dict(range=[0, 100], visible=False), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=10), height=650)
            if pitch_b64: fig_pitch.add_layout_image(source=pitch_b64, x=0, y=100, xref="x", yref="y", sizex=100, sizey=100, sizing="stretch", layer="below")
            
            loc = selected_shot.get('location', 19)
            if pd.isna(loc): loc = 19
            px_x, px_y = PITCH_MAP.get(int(loc), (50, 50))
            if icon_b64: fig_pitch.add_layout_image(source=icon_b64, x=px_x, y=px_y, xref="x", yref="y", sizex=8, sizey=8, xanchor="center", yanchor="middle")
            st.plotly_chart(fig_pitch, use_container_width=True, config={'displayModeBar': False})

            st.markdown("---")
            st.markdown("#### 🥅 Miejsce strzału")
            fig_goal = go.Figure()
            fig_goal.update_layout(xaxis=dict(range=[0, 100], visible=False), yaxis=dict(range=[0, 100], visible=False), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0), height=220)
            if goal_b64: fig_goal.add_layout_image(source=goal_b64, x=0, y=100, xref="x", yref="y", sizex=100, sizey=100, sizing="stretch", layer="below")
            
            sp = selected_shot.get('shot_place', 5)
            if pd.isna(sp): sp = 5
            gx, gy = GOAL_MAP.get(int(sp), (50, 50))
            if icon_b64: fig_goal.add_layout_image(source=icon_b64, x=gx, y=gy, xref="x", yref="y", sizex=8, sizey=8, xanchor="center", yanchor="middle")
            st.plotly_chart(fig_goal, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Brak zarejestrowanych strzałów w tym meczu.")

    # (Tutaj zostaje kod Match Momentum, pominąłem go dla zwięzłości, ale Ty go zostaw!)

    st.markdown("---")

    # --- MATCH MOMENTUM ---
    with st.expander("📊 Wskaźnik zagrożenia (Match Momentum) - Kliknij, aby rozwinąć", expanded=False):
        
        def calculate_threat(row):
            points = 0
            if row['is_goal'] == 1:
                points = 5
            elif row['event_type_name'] == 'Attempt (Strzał)':
                points = 3
            elif row['event_type_name'] == 'Corner (Rożny)':
                points = 1
            
            if row['event_team'] == home_team:
                return points
            elif row['event_team'] == away_team:
                return -points
            else:
                return 0

        match_events['threat'] = match_events.apply(calculate_threat, axis=1)

        bins = [-1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 120]
        base_labels = [
            '1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '31-35', '36-40', '41-45+',
            '46-50', '51-55', '56-60', '61-65', '66-70', '71-75', '76-80', '81-85', '86-90+'
        ]
        
        match_events['time_bin'] = pd.cut(match_events['time'], bins=bins, labels=base_labels, right=True)

        momentum_df = match_events.groupby('time_bin', observed=False)['threat'].sum().reset_index()
        momentum_df['threat'] = momentum_df['threat'].fillna(0)
        momentum_df['time_bin'] = momentum_df['time_bin'].astype(str)

        dummy_row = pd.DataFrame([{'time_bin': 'PRZERWA', 'threat': 0}])
        momentum_df = pd.concat([momentum_df.iloc[:9], dummy_row, momentum_df.iloc[9:]], ignore_index=True)

        momentum_df['Dominacja'] = momentum_df['threat'].apply(
            lambda x: home_team if x > 0 else (away_team if x < 0 else 'Brak / Równowaga')
        )

        all_categories = base_labels[:9] + ['PRZERWA'] + base_labels[9:]

        fig_momentum = px.bar(
            momentum_df, 
            x='time_bin', 
            y='threat', 
            color='Dominacja',
            color_discrete_map={
                home_team: '#1f77b4',
                away_team: '#d62728',
                'Brak / Równowaga': '#D3D3D3'
            }
        )

        fig_momentum.update_layout(
            barmode='relative',
            yaxis=dict(title="", zeroline=True, zerolinewidth=2, zerolinecolor='black', showticklabels=False),
            xaxis=dict(
                title="", showticklabels=False, type='category', 
                categoryorder='array', categoryarray=all_categories   
            ),
            showlegend=True,
            legend_title="Inicjatywa",
            height=350, margin=dict(t=30, b=10)
        )

        fig_momentum.add_vline(x='PRZERWA', line_width=2, line_dash="dash", line_color="gray")
        fig_momentum.add_annotation(
            x='PRZERWA', y=1.05, yref="paper", text="Przerwa", 
            showarrow=False, font=dict(color="gray", size=12)
        )

        spacer_left, col_chart, spacer_right = st.columns([1.5, 7, 1.5])
        
        with col_chart:
            st.plotly_chart(fig_momentum, use_container_width=True)
            st.caption(f"**Jak czytać wykres?** Słupki w górę = {home_team}, słupki w dół = {away_team}. Wykres prezentuje skumulowane akcje ofensywne w 5-minutowych przedziałach.")