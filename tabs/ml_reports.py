import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import data_loader as dl
import json
import base64
import tempfile
import os
import warnings
import requests
from fpdf import FPDF
from google import genai


# Wyciszamy irytujące ostrzeżenie StatsBomb o braku loginu (Open Data)
warnings.filterwarnings("ignore", message="credentials were not supplied")

# ==========================================
# 🛠️ POMOCNICZE FUNKCJE WIZUALNE I PDF
# ==========================================
def get_base64_image(file_path):
    try:
        with open(file_path, "rb") as img_file:
            return f"data:image/svg+xml;base64,{base64.b64encode(img_file.read()).decode()}"
    except FileNotFoundError:
        return None

def download_unicode_fonts():
    """Pobiera czcionki Roboto (wspierające polskie znaki) do katalogu roboczego."""
    reg_font = "Roboto-Regular.ttf"
    bold_font = "Roboto-Bold.ttf"
    try:
        if not os.path.exists(reg_font):
            r = requests.get("https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Regular.ttf", allow_redirects=True)
            with open(reg_font, 'wb') as f: f.write(r.content)
        if not os.path.exists(bold_font):
            r = requests.get("https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Bold.ttf", allow_redirects=True)
            with open(bold_font, 'wb') as f: f.write(r.content)
        return reg_font, bold_font
    except Exception as e:
        print(f"Nie udalo sie pobrac czcionki: {e}")
        return None, None

def add_pdf_figure_inline(pdf, fig, x, y, w, fig_type="standard"):
    """Wkleja wykres do PDF w konkretnym miejscu (X, Y) z zachowaniem proporcji. Zwraca wysokość grafiki."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        try:
            if fig_type == "pitch":
                fig.write_image(tmpfile.name, format="png", width=400, height=600)
                pdf.image(tmpfile.name, x=x, y=y, w=w)
                return w * 1.5  # proporcja 1:1.5
            elif fig_type == "radar":
                # Zwiększona szerokość obrazka bazowego, aby pomieścić szersze marginesy radaru
                fig.write_image(tmpfile.name, format="png", width=700, height=500)
                pdf.image(tmpfile.name, x=x, y=y, w=w)
                return w * (500/700)
            elif fig_type == "goal":
                # Specjalne proporcje dla bramki (600x350 pikseli)
                fig.write_image(tmpfile.name, format="png", width=600, height=350)
                pdf.image(tmpfile.name, x=x, y=y, w=w)
                return w * (350/600)
            else:
                fig.write_image(tmpfile.name, format="png", width=800, height=400)
                pdf.image(tmpfile.name, x=x, y=y, w=w)
                return w * 0.5
        except Exception:
            pdf.set_xy(x, y)
            pdf.set_font(pdf.font_family, 'I', 10)
            pdf.cell(w, 10, txt="[Blad eksportu wykresu]", ln=True)
            return 10
        finally:
            tmpfile.close()
            if os.path.exists(tmpfile.name):
                os.remove(tmpfile.name)

def create_pdf_report(ai_json, entity_name, report_type, figures_dict, stats_payload):
    """Generuje plik PDF zachowując wszystkie polskie znaki oraz układ kolumnowy."""
    pdf = FPDF()
    
    # Inicjalizacja polskich czcionek
    reg_font, bold_font = download_unicode_fonts()
    font_fam = "Arial"
    if reg_font and bold_font:
        try:
            pdf.add_font("Roboto", "", reg_font)
            pdf.add_font("Roboto", "B", bold_font)
            font_fam = "Roboto"
        except Exception:
            pass
            
    def safe_text(text):
        # 1. Zabezpieczenie: jeśli AI zwróci słownik/listę, rozpakuj to do czystego tekstu
        if isinstance(text, list):
            text = " ".join([str(x) for x in text])
        elif isinstance(text, dict):
            parts = []
            for k, v in text.items():
                if isinstance(v, list): v = " ".join([str(x) for x in v])
                parts.append(f"{k.capitalize()}: {v}")
            text = " | ".join(parts)
            
        # 2. Usuwamy gwiazdki markdown
        text = str(text).replace('**', '') 
        
        # 3. Awaryjne podmienianie polskich znaków
        if font_fam == "Arial":
            replacements = {'ą':'a', 'ć':'c', 'ę':'e', 'ł':'l', 'ń':'n', 'ó':'o', 'ś':'s', 'ź':'z', 'ż':'z',
                            'Ą':'A', 'Ć':'C', 'Ę':'E', 'Ł':'L', 'Ń':'N', 'Ó':'O', 'Ś':'S', 'Ź':'Z', 'Ż':'Z'}
            for k, v in replacements.items():
                text = text.replace(k, v)
        return text

    pdf.add_page()
    pdf.set_font(font_fam, 'B', 16)
    pdf.cell(200, 10, txt=safe_text(f"Raport Skautingowy: {entity_name}" if report_type == "Gracz" else f"Raport Taktyczny Zespolu: {entity_name}"), ln=True, align='C')
    pdf.ln(5)

    # 1. Podsumowanie Statystyczne
    pdf.set_font(font_fam, 'B', 12)
    pdf.cell(200, 10, txt=safe_text("Podsumowanie Statystyczne:"), ln=True)
    pdf.set_font(font_fam, size=11)
    if report_type == "Gracz":
        pdf.cell(200, 6, txt=safe_text(f"Rozegrane minuty w analizowanym okresie: {stats_payload['Minuty']}"), ln=True)
        pdf.ln(2)
        pdf.set_font(font_fam, 'B', 11)
        pdf.cell(200, 6, txt=safe_text("Kluczowe Percentyle:"), ln=True)
        pdf.set_font(font_fam, size=10)
        for k, v in stats_payload['Percentyle'].items():
            pdf.cell(200, 6, txt=safe_text(f"  - {k}: {v}. percentyl"), ln=True)
    pdf.ln(5)
    
    # 2. Profil
    if "profil" in ai_json:
        pdf.set_font(font_fam, 'B', 12)
        pdf.cell(200, 10, txt=safe_text("1. Profil i charakterystyka"), ln=True)
        pdf.set_font(font_fam, size=11)
        pdf.multi_cell(0, 7, txt=safe_text(ai_json["profil"]))
        pdf.ln(5)

    # 3. DNA / Atuty (Zależne od układu Gracz/Drużyna)
    if "atuty_i_braki" in ai_json:
        if pdf.get_y() > 200: pdf.add_page()
        pdf.set_font(font_fam, 'B', 12)
        pdf.cell(200, 10, txt=safe_text("2. DNA taktyczne (atuty i braki)"), ln=True)
        
        start_y = pdf.get_y()
        pdf.set_font(font_fam, size=11)
        
        if report_type == "Gracz":
            # Dla gracza: węższa kolumna, radar po prawej
            pdf.multi_cell(110, 7, txt=safe_text(ai_json["atuty_i_braki"]))
            end_y_text = pdf.get_y()
            if "radar" in figures_dict:
                h = add_pdf_figure_inline(pdf, figures_dict["radar"], x=120, y=start_y, w=80, fig_type="radar")
                end_y_img = start_y + h
            else:
                end_y_img = start_y
            pdf.set_y(max(end_y_text, end_y_img) + 8)
        else:
            # Dla drużyny: pełna szerokość bez wykresu po prawej
            pdf.multi_cell(0, 7, txt=safe_text(ai_json["atuty_i_braki"]))
            pdf.ln(5)

    # 4. Dystrybucja (Zależne od układu Gracz/Drużyna)
    if "dystrybucja" in ai_json:
        if pdf.get_y() > 180: pdf.add_page()
        pdf.set_font(font_fam, 'B', 12)
        pdf.cell(200, 10, txt=safe_text("3. Dystrybucja i kreacja"), ln=True)
        
        start_y = pdf.get_y()
        pdf.set_font(font_fam, size=11)
        
        if report_type == "Gracz":
            # Dla gracza: węższa kolumna, boisko po prawej
            pdf.multi_cell(110, 7, txt=safe_text(ai_json["dystrybucja"]))
            end_y_text = pdf.get_y()
            if "pitch" in figures_dict:
                h = add_pdf_figure_inline(pdf, figures_dict["pitch"], x=135, y=start_y, w=55, fig_type="pitch")
                end_y_img = start_y + h
            else:
                end_y_img = start_y
            pdf.set_y(max(end_y_text, end_y_img) + 8)
        else:
            # Dla drużyny: pełna szerokość bez wykresu po prawej
            pdf.multi_cell(0, 7, txt=safe_text(ai_json["dystrybucja"]))
            pdf.ln(5)

    # 5. Aktywność Strzelecka (Nowa sekcja dla Gracza)
    if "strzaly" in ai_json and report_type == "Gracz":
        if pdf.get_y() > 140: pdf.add_page()
        pdf.set_font(font_fam, 'B', 12)
        pdf.cell(200, 10, txt=safe_text("4. Aktywność strzelecka"), ln=True)
        
        pdf.set_font(font_fam, size=11)
        pdf.multi_cell(0, 7, txt=safe_text(ai_json["strzaly"]))
        pdf.ln(5)

        y_figs = pdf.get_y()
        h1 = h2 = 0
        if "shots_map" in figures_dict:
            h1 = add_pdf_figure_inline(pdf, figures_dict["shots_map"], x=20, y=y_figs, w=60, fig_type="pitch")
        if "goal_face" in figures_dict:
            h2 = add_pdf_figure_inline(pdf, figures_dict["goal_face"], x=90, y=y_figs + 15, w=100, fig_type="goal")
            
        pdf.set_y(y_figs + max(h1, h2) + 8)
        
    # Wykresy drużynowe rendering pełnej szerokości
    if "team_charts_pdf" in figures_dict:
        for fig in figures_dict["team_charts_pdf"]:
            if pdf.get_y() > 220: pdf.add_page()
            h = add_pdf_figure_inline(pdf, fig, x=10, y=pdf.get_y(), w=190, fig_type="standard")
            pdf.set_y(pdf.get_y() + h + 5)

    # 6. Werdykt
    if "werdykt" in ai_json:
        pdf.ln(5)
        pdf.set_font(font_fam, 'B', 12)
        pdf.cell(200, 10, txt=safe_text("Ostateczna ocena"), ln=True)
        pdf.set_font(font_fam, 'I', 11)
        pdf.multi_cell(0, 7, txt=safe_text(ai_json["werdykt"]))

    return pdf.output(dest='S').encode('latin-1', 'ignore') if font_fam == "Arial" else pdf.output(dest='S')

# SILNIK AI
def generate_gemini_report(data_dict, report_type, entity_name, api_key):
    if not api_key: return None
    client = genai.Client(api_key=api_key)

    if report_type == "Gracz":
        system_instruction = """Jesteś Analitykiem Piłkarskim. 
        Otrzymasz statystyki p90 oraz percentyle (0-100).
        Zwróć wynik WYŁĄCZNIE w formacie JSON (bez znaczników markdown).
        
        🔴 WAŻNE ZASADY FORMATOWANIA 🔴
        1. Zachowaj ścisłą jednolitość percentyli. Używaj formatu: 'X percentyl' (np. '24 percentyl', '67 percentyl').
        2. ZABRANIA CI SIĘ używania znaku '%' (Nigdy nie pisz '24%').
        3. ZABRANIA CI SIĘ używania znaczników Markdown (np. gwiazdek ** do pogrubień). Tekst ma być czysty.
        
        Struktura JSON:
        {
            "profil": "Styl gry. Oceń próbę minutową.",
            "atuty_i_braki": "Siły i słabości bazując na twardych liczbach i percentylach.",
            "dystrybucja": "Ocena podawania i kreacji.",
            "strzaly": "Ocena aktywności strzeleckiej i wykończenia bazując na liczbach.",
            "werdykt": "Krótkie podsumowanie."
        }"""
    else:
        system_instruction = """Jesteś Analitykiem Taktycznym. 
        Zwróć wynik WYŁĄCZNIE w formacie JSON (bez znaczników markdown).
        UWAGA: Wszystkie wartości w JSON muszą być JEDNYM, CZYSTYM STRINGIEM (tekstem).
        NIE używaj zagnieżdżonych list ani słowników.
        {
            "profil": "Styl gry zespołu.",
            "atuty_i_braki": "Kluczowe mocne i słabe strony.",
            "dystrybucja": "Jak drużyna operuje piłką.",
            "werdykt": "Podsumowanie potencjału zespołu."
        }"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Dane dla {entity_name}:\n{json.dumps(data_dict)}",
            config={
                "system_instruction": system_instruction,
                "temperature": 0.15
            }
        )
        raw_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"🚨 Błąd AI: {str(e)}")
        return None

# ==========================================
# 📊 BAZA DANYCH
# ==========================================
@st.cache_data(show_spinner=False)
def build_scouting_database(_matches_df, team_name):
    team_matches = _matches_df[(_matches_df['home_team'] == team_name) | (_matches_df['away_team'] == team_name)]
    
    all_events = []
    for match_id in team_matches['match_id']:
        ev = dl.get_match_events(match_id)
        if not ev.empty: all_events.append(ev)
        
    if not all_events: return pd.DataFrame(), pd.DataFrame()
    full_df = pd.concat(all_events, ignore_index=True)

    player_mins = full_df.groupby(['match_id', 'player'])['minute'].max().reset_index()
    total_mins = player_mins.groupby('player')['minute'].sum().reset_index()
    total_mins.rename(columns={'minute': 'minutes_played'}, inplace=True)
    
    total_mins = total_mins[total_mins['minutes_played'] >= 90]

    valid_players = total_mins['player'].tolist()
    filtered_df = full_df[full_df['player'].isin(valid_players)].copy()

    stats = []
    for player, group in filtered_df.groupby('player'):
        mins = total_mins[total_mins['player'] == player]['minutes_played'].values[0]
        stats.append({
            'player': player, 'minutes_played': mins,
            'Akcje Defensywne': len(group[group['type'].isin(['Interception', 'Block', 'Clearance', 'Duel'])]),
            'Kreatywność': len(group[(group['type'] == 'Pass') & (group.get('pass_shot_assist') == True)]),
            'Rozegranie': len(group[group['type'] == 'Pass']),
            'Strzały': len(group[group['type'] == 'Shot']),
            'Prowadzenie Piłki': len(group[group['type'] == 'Carry']),
            'Presja': len(group[group['type'] == 'Pressure'])
        })
    stats_df = pd.DataFrame(stats)
    for m in ['Akcje Defensywne', 'Kreatywność', 'Rozegranie', 'Strzały', 'Prowadzenie Piłki', 'Presja']:
        stats_df[f'{m}_p90'] = (stats_df[m] / stats_df['minutes_played']) * 90.0
        stats_df[f'{m}_pct'] = (stats_df[f'{m}_p90'].rank(pct=True).fillna(0) * 100).astype(int)
        
    return full_df, stats_df

# ==========================================
# 🖥️ GŁÓWNY INTERFEJS (HYBRYDA Z SESSION STATE)
# ==========================================
def render(matches_df):
    st.title("🧠 Raport skautingowy AI")
    st.markdown("---")

    if "report_data" not in st.session_state:
        st.session_state.report_data = None

    try:
        user_api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("🚨 Brak klucza API w `.streamlit/secrets.toml`!")
        return

    report_type = st.radio("Poziom analizy:", ["Gracz", "Drużyna"], horizontal=True)
    all_teams = sorted(list(set(matches_df['home_team']).union(set(matches_df['away_team']))))
    selected_team = st.selectbox("🛡️ Wybierz drużynę:", all_teams)

    entity_name = selected_team
    
    with st.spinner(f"Wczytywanie danych dla {selected_team}..."):
        full_events_df, player_stats_df = build_scouting_database(matches_df, selected_team)

    if report_type == "Gracz":
        if player_stats_df.empty:
            st.warning("Brak danych do analizy graczy w tym zespole.")
            return
        
        team_events = full_events_df[full_events_df['team'] == selected_team]
        valid_players = [p for p in team_events['player'].dropna().unique() if p in player_stats_df['player'].values]
        
        if not valid_players:
            st.warning("Brak zawodników z odpowiednią liczbą minut w wybranym zespole.")
            return
            
        entity_name = st.selectbox("🏃 Wybierz zawodnika:", sorted(valid_players))

    if st.button("🚀 Generuj Kompleksowy Raport", type="primary"):
        with st.spinner("Przetwarzanie danych, generowanie wykresów i wnioskowanie AI..."):
            figures_dict = {}
            
            if report_type == "Gracz":
                player_data = player_stats_df[player_stats_df['player'] == entity_name].iloc[0]
                stats_payload = {
                    "Typ": "Gracz", "Minuty": int(player_data['minutes_played']),
                    "Percentyle": {
                        "Strzały": int(player_data['Strzały_pct']), 
                        "Kreacja": int(player_data['Kreatywność_pct']),
                        "Rozegranie": int(player_data['Rozegranie_pct']), 
                        "Prowadzenie": int(player_data['Prowadzenie Piłki_pct']),
                        "Obrona": int(player_data['Akcje Defensywne_pct']), 
                        "Presja": int(player_data['Presja_pct'])
                    }
                }
            else:
                team_ev = full_events_df[full_events_df['team'] == entity_name]
                stats_payload = {
                    "Typ": "Drużyna", "Liczba_akcji": len(team_ev),
                    "Gole": len(team_ev[team_ev['shot_outcome'] == 'Goal']),
                    "Podania_ogółem": len(team_ev[team_ev['type'] == 'Pass'])
                }

            ai_json = generate_gemini_report(stats_payload, report_type, entity_name, user_api_key)
            
            if ai_json:
                if report_type == "Gracz":
                    categories = ['Akcje Defensywne', 'Kreatywność', 'Rozegranie', 'Strzały', 'Prowadzenie Piłki', 'Presja']
                    vals = [player_data[f'{c}_pct'] for c in categories]
                    
                    # 1. RADAR DO APLIKACJI (Ciemny motyw)
                    fig_radar_app = go.Figure(go.Scatterpolar(
                        r=vals+[vals[0]], theta=categories+[categories[0]], fill='toself', 
                        line=dict(color='#2ecc71', width=2), fillcolor='rgba(46, 204, 113, 0.4)'
                    ))
                    fig_radar_app.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(color='white', size=11), gridcolor='rgba(255,255,255,0.2)'),
                            angularaxis=dict(tickfont=dict(color='white', size=12), gridcolor='rgba(255,255,255,0.2)'),
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        showlegend=False, height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=50, t=20, b=20)
                    )
                    
                    # 2. RADAR DO PDF (Jasny motyw, z DUŻYMI marginesami i powiększoną czcionką)
                    fig_radar_pdf = go.Figure(go.Scatterpolar(
                        r=vals+[vals[0]], theta=categories+[categories[0]], fill='toself', 
                        line=dict(color='#2ecc71', width=2), fillcolor='rgba(46, 204, 113, 0.4)'
                    ))
                    fig_radar_pdf.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True, 
                                range=[0, 100], 
                                tickfont=dict(color='black', size=16), # Powiększona skala (0, 20, 40...)
                                gridcolor='rgba(0,0,0,0.15)'
                            ),
                            angularaxis=dict(
                                tickfont=dict(color='black', size=19), # Powiększone nazwy statystyk
                                gridcolor='rgba(0,0,0,0.15)'
                            ),
                            bgcolor='rgba(255,255,255,1)'
                        ),
                        showlegend=False, 
                        height=500, 
                        width=700, 
                        paper_bgcolor='rgba(255,255,255,1)', 
                        plot_bgcolor='rgba(255,255,255,1)', 
                        margin=dict(l=50, r=150, t=50, b=50)  # Powiększone marginesy, aby zmieścić większe teksty
                    )
                    
                    figures_dict["radar_app"] = fig_radar_app
                    figures_dict["radar"] = fig_radar_pdf

                    player_ev = full_events_df[full_events_df['player'] == entity_name]
                    last_5_matches = player_ev['match_id'].unique()[-5:]
                    
                    # ==========================================
                    # 🗺️ MAPA PODAŃ Z PROGRESSIVE (Tylko zapis danych)
                    # ==========================================
                    match_passes = player_ev[(player_ev['match_id'].isin(last_5_matches)) & (player_ev['type'] == 'Pass')].copy()

                    if not match_passes.empty:
                        P_LEFT, P_RIGHT, P_BOTT, P_TOP = 1.0, 99.0, 1.0, 99.0
                        p_width, p_height = P_RIGHT - P_LEFT, P_TOP - P_BOTT

                        match_passes['start_x_scaled'] = P_LEFT + ((match_passes['location_y'] / 80.0) * p_width)
                        match_passes['start_y_scaled'] = P_BOTT + ((match_passes['location_x'] / 120.0) * p_height)
                        match_passes['end_x_scaled'] = P_LEFT + ((match_passes['pass_end_y'] / 80.0) * p_width)
                        match_passes['end_y_scaled'] = P_BOTT + ((match_passes['pass_end_x'] / 120.0) * p_height)
                        
                        dist_start = np.sqrt((120 - match_passes['location_x'])**2 + (40 - match_passes['location_y'])**2)
                        dist_end = np.sqrt((120 - match_passes['pass_end_x'])**2 + (40 - match_passes['pass_end_y'])**2)
                        match_passes['is_progressive'] = (match_passes['pass_outcome'].isna()) & ((dist_start - dist_end) >= 10.0)

                        # Wyłącznie zapisujemy tabelę (rysowanie na dole dynamicznie do PDF)
                        figures_dict["match_passes_df"] = match_passes

                    # ==========================================
                    # 🎯 MAPA STRZAŁÓW I ŚWIATŁO BRAMKI
                    # ==========================================
                    match_shots = player_ev[(player_ev['match_id'].isin(last_5_matches)) & (player_ev['type'] == 'Shot')].copy()
                    
                    if not match_shots.empty:
                        # Rzut boiska (Strzały)
                        match_shots['start_x_scaled'] = P_LEFT + ((match_shots['location_y'] / 80.0) * p_width)
                        match_shots['start_y_scaled'] = P_BOTT + ((match_shots['location_x'] / 120.0) * p_height)
                        
                        fig_shots = go.Figure()
                        img = get_base64_image("data/img/pitch.svg")
                        if img:
                            fig_shots.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=100, sizex=100, sizey=100, sizing="stretch", opacity=0.9, layer="below"))
                            
                        goals = match_shots[match_shots['shot_outcome'] == 'Goal']
                        no_goals = match_shots[match_shots['shot_outcome'] != 'Goal']

                        if not no_goals.empty:
                            fig_shots.add_trace(go.Scatter(x=no_goals['start_x_scaled'], y=no_goals['start_y_scaled'], mode='markers', marker=dict(size=12, color='#e74c3c', symbol='x', opacity=0.8), showlegend=False))
                        if not goals.empty:
                            fig_shots.add_trace(go.Scatter(x=goals['start_x_scaled'], y=goals['start_y_scaled'], mode='markers', marker=dict(size=16, color='#2ecc71', symbol='circle', line=dict(width=2, color='white')), showlegend=False))
                            
                        fig_shots.update_layout(
                            xaxis=dict(range=[0, 100], visible=False), 
                            yaxis=dict(range=[0, 100], visible=False, scaleanchor="x", scaleratio=1.5),
                            margin=dict(l=0, r=0, t=0, b=0), height=600, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                        )
                        figures_dict["shots_map"] = fig_shots
                        
                        # Światło bramki
                        match_shots['end_y'] = match_shots['shot_end_location'].apply(lambda loc: loc[1] if isinstance(loc, list) and len(loc) > 1 else np.nan)
                        match_shots['end_z'] = match_shots['shot_end_location'].apply(lambda loc: loc[2] if isinstance(loc, list) and len(loc) > 2 else 0.0)
                        valid_goal_shots = match_shots.dropna(subset=['end_y']).copy()
                        
                        if not valid_goal_shots.empty:
                            G_LEFT, G_RIGHT, G_BOTTOM, G_TOP = 14.17, 85.83, 14.29, 62.86
                            g_width, g_height = G_RIGHT - G_LEFT, G_TOP - G_BOTTOM
                            
                            fig_goal = go.Figure()
                            goal_img = get_base64_image("data/img/goal.svg")
                            if goal_img:
                                fig_goal.add_layout_image(dict(source=goal_img, xref="x", yref="y", x=0, y=100, sizex=100, sizey=100, sizing="stretch", opacity=1.0, layer="below"))
                                
                            # Słownik ikon strzałów
                            outcome_icons = {
                                'Saved': 'data/img/save.svg',
                                'Saved to Post': 'data/img/save.svg',
                                'Saved Off Target': 'data/img/save.svg',
                                'Blocked': 'data/img/block.svg',
                                'Off T': 'data/img/miss.svg',
                                'Wayward': 'data/img/miss.svg'
                            }
                                
                            for _, row in valid_goal_shots.iterrows():
                                goal_x = G_LEFT + ((row['end_y'] - 36.0) / 8.0) * g_width
                                goal_y = G_BOTTOM + ((row['end_z'] - 0.0) / 2.67) * g_height
                                clamped_x = max(2.5, min(goal_x, 97.5))
                                clamped_y = max(2.0, min(goal_y, 97.5))
                                outcome = row['shot_outcome']
                                
                                specific_icon_path = outcome_icons.get(outcome)
                                
                                if specific_icon_path:
                                    encoded_specific_icon = get_base64_image(specific_icon_path)
                                    if encoded_specific_icon:
                                        icon_size = 7 if "miss.svg" in specific_icon_path else 14
                                        fig_goal.add_layout_image(dict(
                                            source=encoded_specific_icon, xref="x", yref="y",
                                            x=clamped_x, y=clamped_y, sizex=icon_size, sizey=icon_size, xanchor="center", yanchor="middle",
                                            layer="above", sizing="contain"
                                        ))
                                        
                                        # Niewidzialny marker zapobiegający problemom z legendą/hoverem
                                        fig_goal.add_trace(go.Scatter(
                                            x=[clamped_x], y=[clamped_y], mode='markers', marker=dict(size=14, opacity=0),
                                            showlegend=False
                                        ))
                                else:
                                    # Zielona kropka dla Gola lub żółta awaryjna
                                    color_marker = '#2ecc71' if outcome == 'Goal' else '#f39c12'
                                    fig_goal.add_trace(go.Scatter(
                                        x=[clamped_x], y=[clamped_y], mode='markers',
                                        marker=dict(size=14, color=color_marker, line=dict(color='white', width=2.0), symbol='circle'),
                                        showlegend=False
                                    ))
                                
                            fig_goal.update_layout(
                                xaxis=dict(range=[0, 100], visible=False), 
                                # Wymuszenie proporcji światła bramki (350 / 600 = 0.5833)
                                yaxis=dict(range=[0, 100], visible=False, scaleanchor="x", scaleratio=350/600),
                                margin=dict(l=0, r=0, t=0, b=0), height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                            )
                            figures_dict["goal_face"] = fig_goal

                else:
                    team_matches = matches_df[(matches_df['home_team'] == entity_name) | (matches_df['away_team'] == entity_name)].sort_values(by='match_date', ascending=True).tail(5)
                    figures_dict["team_charts_app"] = []
                    figures_dict["team_charts_pdf"] = []
                    
                    for _, match in team_matches.iterrows():
                        ev = dl.get_match_events(match['match_id'])
                        if ev.empty: continue
                        max_minute = ev['minute'].max() + 1
                        
                        shots = ev[ev['type'] == 'Shot'].copy()
                        if 'shot_statsbomb_xg' not in shots.columns: shots['shot_statsbomb_xg'] = 0.05
                        
                        fig_xg = go.Figure()
                        for team, color in zip([match['home_team'], match['away_team']], ['#3498db', '#e74c3c']):
                            team_shots = shots[shots['team'] == team].copy().sort_values(by='minute')
                            team_shots['cum_xG'] = team_shots['shot_statsbomb_xg'].cumsum()
                            x_vals = [0] + team_shots['minute'].tolist() + [max_minute]
                            y_vals = [0] + team_shots['cum_xG'].tolist() + [team_shots['cum_xG'].max() if not team_shots.empty else 0]
                            fig_xg.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', line_shape='hv', name=team, line=dict(color=color, width=3)))
                        
                        # Wersja UI (Ciemna)
                        fig_xg_app = go.Figure(fig_xg)
                        fig_xg_app.update_layout(title=f"xG: vs {match['away_team'] if match['home_team'] == entity_name else match['home_team']}", xaxis=dict(range=[0, max_minute]), height=300, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                        # Wersja PDF (Jasna)
                        fig_xg_pdf = go.Figure(fig_xg)
                        fig_xg_pdf.update_layout(title=f"xG: vs {match['away_team'] if match['home_team'] == entity_name else match['home_team']}", xaxis=dict(range=[0, max_minute]), height=300, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='white', plot_bgcolor='white', font=dict(color='black'))
                        
                        actions = ev[ev['type'].isin(['Pass', 'Carry', 'Shot'])].copy()
                        actions_per_min = actions.groupby(['minute', 'team']).size().reset_index(name='count')
                        timeline = pd.DataFrame({'minute': range(0, max_minute + 1)})
                        timeline = timeline.merge(actions_per_min[actions_per_min['team'] == match['home_team']][['minute', 'count']], on='minute', how='left').rename(columns={'count': 'home'})
                        timeline = timeline.merge(actions_per_min[actions_per_min['team'] == match['away_team']][['minute', 'count']], on='minute', how='left').rename(columns={'count': 'away'})
                        timeline = timeline.fillna(0)
                        timeline['momentum'] = (timeline['home'] - timeline['away']).rolling(window=5, min_periods=1).mean()
                        
                        fig_mom = go.Figure()
                        fig_mom.add_trace(go.Scatter(x=timeline['minute'], y=np.where(timeline['momentum']>0, timeline['momentum'], 0), fill='tozeroy', line=dict(width=0), fillcolor='rgba(52, 152, 219, 0.7)', name=match['home_team']))
                        fig_mom.add_trace(go.Scatter(x=timeline['minute'], y=np.where(timeline['momentum']<0, timeline['momentum'], 0), fill='tozeroy', line=dict(width=0), fillcolor='rgba(231, 76, 60, 0.7)', name=match['away_team']))
                        fig_mom.add_hline(y=0, line_color="white", opacity=0.5)
                        
                        # Wersja UI (Ciemna)
                        fig_mom_app = go.Figure(fig_mom)
                        fig_mom_app.update_layout(title="Match Momentum", xaxis=dict(range=[0, max_minute]), yaxis=dict(showticklabels=False), height=300, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                        # Wersja PDF (Jasna)
                        fig_mom_pdf = go.Figure(fig_mom)
                        fig_mom_pdf.update_layout(title="Match Momentum", xaxis=dict(range=[0, max_minute]), yaxis=dict(showticklabels=False), height=300, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='white', plot_bgcolor='white', font=dict(color='black'))

                        figures_dict["team_charts_app"].extend([fig_xg_app, fig_mom_app])
                        figures_dict["team_charts_pdf"].extend([fig_xg_pdf, fig_mom_pdf])

                st.session_state.report_data = {
                    "entity_name": entity_name,
                    "report_type": report_type,
                    "stats_payload": stats_payload,
                    "ai_json": ai_json,
                    "figures_dict": figures_dict
                }

    # ========================================================
    # 🎨 WIDOK RAPORTU UI
    # ========================================================
    if st.session_state.report_data is not None:
        rep = st.session_state.report_data
        
        st.markdown(f"## 📋 Raport: {rep['entity_name']}")
        st.markdown("---")
        
        if rep['report_type'] == "Gracz":
            st.markdown(f"**Rozegrane minuty w analizowanym okresie:** {rep['stats_payload']['Minuty']}")
            st.markdown("**Kluczowe percentyle (na tle ligi):**")
            cols = st.columns(6)
            for idx, (k, v) in enumerate(rep['stats_payload']['Percentyle'].items()):
                cols[idx].metric(k, f"{v} perc.")
            st.markdown("---")

        st.markdown("### 1. Profil i charakterystyka gry")
        st.write(str(rep['ai_json'].get("profil", "")).replace('**', ''))
        st.markdown("---")

        if rep['report_type'] == "Gracz":
            st.markdown("### 2. DNA taktyczne (atuty i braki)")
            col_ai_1, col_viz_1 = st.columns(2)
            with col_ai_1: st.write(str(rep['ai_json'].get("atuty_i_braki", "")).replace('**', ''))
            with col_viz_1:
                if "radar_app" in rep['figures_dict']: st.plotly_chart(rep['figures_dict']["radar_app"], width="stretch")
            st.markdown("---")

            st.markdown("### 3. Dystrybucja i kreacja (ostatnie 5 meczów)")
            
            # CSS WYMUSZAJĄCY BŁĘKITNE CHECKBOXY W STREAMLIT
            st.markdown("""
            <style>
            div[data-testid="stCheckbox"] label span[data-baseweb="checkbox"] div[data-checked="true"] {
                background-color: #3498db !important;
                border-color: #3498db !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            col_ai_2, col_viz_2 = st.columns(2)
            with col_ai_2: 
                st.write(str(rep['ai_json'].get("dystrybucja", "")).replace('**', ''))
                st.markdown("<br>**Filtruj rodzaj podań na wykresie i w raporcie PDF:**", unsafe_allow_html=True)
                show_prog_ml = st.checkbox("🔵 Progresywne podania", value=True, key="ml_prog")
                show_succ_ml = st.checkbox("🟢 Celne podania", value=True, key="ml_succ")
                show_fail_ml = st.checkbox("🔴 Niecelne podania (Straty)", value=True, key="ml_fail")
                
            with col_viz_2:
                if "match_passes_df" in rep['figures_dict']:
                    m_passes = rep['figures_dict']["match_passes_df"]
                    
                    fig_pass = go.Figure()
                    img = get_base64_image("data/img/pitch.svg")
                    if img: 
                        fig_pass.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=100, sizex=100, sizey=100, sizing="stretch", opacity=0.9, layer="below"))
                    
                    f_passes = m_passes[m_passes['pass_outcome'].notna()]
                    p_passes = m_passes[m_passes['is_progressive'] == True]
                    s_passes = m_passes[(m_passes['pass_outcome'].isna()) & (m_passes['is_progressive'] == False)]

                    if show_succ_ml and not s_passes.empty:
                        for _, row in s_passes.iterrows():
                            fig_pass.add_annotation(x=row['end_x_scaled'], y=row['end_y_scaled'], ax=row['start_x_scaled'], ay=row['start_y_scaled'], xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='rgba(46, 204, 113, 0.7)')
                        fig_pass.add_trace(go.Scatter(x=s_passes['start_x_scaled'], y=s_passes['start_y_scaled'], mode='markers', marker=dict(size=6, color='#2ecc71'), hoverinfo='none', showlegend=False))

                    if show_prog_ml and not p_passes.empty:
                        for _, row in p_passes.iterrows():
                            fig_pass.add_annotation(x=row['end_x_scaled'], y=row['end_y_scaled'], ax=row['start_x_scaled'], ay=row['start_y_scaled'], xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='rgba(52, 152, 219, 0.9)')
                        fig_pass.add_trace(go.Scatter(x=p_passes['start_x_scaled'], y=p_passes['start_y_scaled'], mode='markers', marker=dict(size=6, color='#3498db', line=dict(width=1, color='white')), hoverinfo='none', showlegend=False))

                    if show_fail_ml and not f_passes.empty:
                        for _, row in f_passes.iterrows():
                            fig_pass.add_annotation(x=row['end_x_scaled'], y=row['end_y_scaled'], ax=row['start_x_scaled'], ay=row['start_y_scaled'], xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=3, arrowcolor='rgba(231, 76, 60, 0.7)')
                        fig_pass.add_trace(go.Scatter(x=f_passes['start_x_scaled'], y=f_passes['start_y_scaled'], mode='markers', marker=dict(size=6, color='#e74c3c'), hoverinfo='none', showlegend=False))
                    
                    fig_pass.update_layout(
                        xaxis=dict(range=[0, 100], visible=False), 
                        yaxis=dict(range=[0, 100], visible=False, scaleanchor="x", scaleratio=1.5), 
                        height=600, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    # Niezwykle ważne: Nadpisujemy grafikę "pitch" przed pobraniem PDF
                    rep['figures_dict']["pitch"] = fig_pass
                    st.plotly_chart(fig_pass, width="stretch")
            st.markdown("---")
            
            if "strzaly" in rep['ai_json']:
                st.markdown("### 4. Aktywność strzelecka (ostatnie 5 meczów)")
                st.write(str(rep['ai_json'].get("strzaly", "")).replace('**', ''))
                
                col_shot_map, col_shot_goal = st.columns(2)
                with col_shot_map:
                    if "shots_map" in rep['figures_dict']: st.plotly_chart(rep['figures_dict']["shots_map"], width="stretch")
                with col_shot_goal:
                    if "goal_face" in rep['figures_dict']: st.plotly_chart(rep['figures_dict']["goal_face"], width="stretch")
                st.markdown("---")
        
        else:
            st.markdown("### 2. Atuty i braki zespołu")
            st.write(str(rep['ai_json'].get("atuty_i_braki", "")).replace('**', ''))
            st.markdown("---")
            st.markdown("### 3. Dystrybucja i kreacja")
            st.write(str(rep['ai_json'].get("dystrybucja", "")).replace('**', ''))
            st.markdown("---")
            st.markdown("### 📊 Analiza ostatnich 5 meczów (xG i Momentum)")
            
            if "team_charts_app" in rep['figures_dict']:
                charts = rep['figures_dict']["team_charts_app"]
                for i in range(0, len(charts), 2):
                    col1, col2 = st.columns(2)
                    col1.plotly_chart(charts[i], use_container_width=True)
                    if i+1 < len(charts):
                        col2.plotly_chart(charts[i+1], use_container_width=True)
                    st.markdown("---")

        st.success(f"**Ostateczna ocena:** {str(rep['ai_json'].get('werdykt', '')).replace('**', '')}")
        
        pdf_bytes = create_pdf_report(rep['ai_json'], rep['entity_name'], rep['report_type'], rep['figures_dict'], rep['stats_payload'])
        st.download_button(
            label="📄 Pobierz raport jako PDF",
            data=pdf_bytes,
            file_name=f"Raport_{rep['entity_name'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )