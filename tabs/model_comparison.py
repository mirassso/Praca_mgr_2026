import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import data_loader as dl
import xg_engine

def render(matches_df):
    st.title("⚖️ Porównanie Modeli xG")
    st.info("W tej zakładce bezpośrednio porównujemy autorskie modele xG z oficjalnym modelem analitycznym StatsBomb. Wybierz algorytm, aby zobaczyć, jak różni się on w interpretacji tych samych strzałów od rynkowego standardu.")
    st.markdown("---")

    if matches_df.empty:
        st.warning("Brak meczów do analizy.")
        return

    # Wybór meczu
    matches_df = matches_df.copy().sort_values(by='match_date', ascending=False)
    matches_df['match_label'] = matches_df['match_date'].astype(str) + " | " + matches_df['home_team'] + " vs " + matches_df['away_team']
    selected_match_label = st.selectbox("🔎 Wybierz mecz do weryfikacji modeli:", matches_df['match_label'].unique(), key="compare_match_select")

    match_row = matches_df[matches_df['match_label'] == selected_match_label].iloc[0]
    match_id = match_row['match_id']

    with st.spinner("Pobieranie strzałów i uruchamianie silników predykcyjnych..."):
        events_df = dl.get_match_events(match_id)

    if events_df.empty or 'type' not in events_df.columns:
        st.warning("Brak danych zdarzeniowych dla tego meczu.")
        return

    shots = events_df[events_df['type'] == 'Shot'].copy()

    if shots.empty:
        st.info("Brak strzałów w tym meczu.")
        return

    # ==========================================
    # 1. OBLICZANIE AUTORSKIEGO xG PRZEZ NASZ SILNIK
    # ==========================================
    shots = xg_engine.calculate_custom_xg(shots)

    if 'shot_statsbomb_xg' not in shots.columns or 'xg_lr' not in shots.columns:
        st.error("Brak wymaganych danych xG do porównania. Upewnij się, że silnik `xg_engine.py` załadował wszystkie pliki .joblib.")
        return

    # ==========================================
    # 2. WYBÓR MODELU AUTORSKIEGO DO PORÓWNANIA
    # ==========================================
    st.markdown("### ⚙️ Wybierz model do konfrontacji")
    model_options = {
        "Regresja Logistyczna (Najlepsza kalibracja)": "xg_lr",
        "Random Forest (Zbalansowany)": "xg_rf",
        "XGBoost (Agresywny)": "xg_xgb"
    }
    
    selected_model_name = st.radio("Aktywny model autorski:", list(model_options.keys()), horizontal=True)
    selected_xg_col = model_options[selected_model_name]

    # WYLICZANIE BŁĘDU (Bezwzględna różnica)
    shots['xg_diff'] = abs(shots['shot_statsbomb_xg'] - shots[selected_xg_col])

    # ==========================================
    # 3. WYKRES: SCATTER PLOT
    # ==========================================
    short_model_name = selected_model_name.split(" (")[0]
    st.markdown(f"### 📊 Scatter Plot: StatsBomb vs {short_model_name}")
    
    fig_scatter = go.Figure()
    
    # Punkty strzałów (kolorowane po wielkości różnicy)
    fig_scatter.add_trace(go.Scatter(
        x=shots['shot_statsbomb_xg'],
        y=shots[selected_xg_col],
        mode='markers',
        marker=dict(
            size=14, 
            color=shots['xg_diff'], 
            colorscale='Inferno', 
            showscale=True,
            colorbar=dict(title="Różnica xG"),
            opacity=0.9, 
            line=dict(width=1, color='white')
        ),
        text=shots['minute'].astype(str) + "' | " + shots['player'] + "<br>Wynik: " + shots['shot_outcome'],
        hovertemplate="<b>%{text}</b><br>StatsBomb xG: %{x:.3f}<br>Autorskie xG: %{y:.3f}<br>Różnica: %{marker.color:.3f}<extra></extra>"
    ))
    
    # Linia idealnej zgodności (y = x)
    fig_scatter.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode='lines',
        line=dict(dash='dash', color='gray', width=2),
        name='Idealna zgodność'
    ))
    
    fig_scatter.update_layout(
        xaxis_title="Oczekiwane Gole - xG (StatsBomb)",
        yaxis_title=f"Oczekiwane Gole - xG ({short_model_name})",
        xaxis=dict(range=[-0.05, 1.05]),
        yaxis=dict(range=[-0.05, 1.05]),
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    fig_scatter.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    fig_scatter.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ==========================================
    # 4. TABELA ROZBIEŻNOŚCI
    # ==========================================
    st.markdown("---")
    st.markdown("### ⚠️ Największe rozbieżności w ocenie strzałów")

    # Tabela 10 strzałów z największą różnicą
    top_diffs = shots.sort_values(by='xg_diff', ascending=False)[
        ['minute', 'player', 'team', 'shot_outcome', 'shot_statsbomb_xg', selected_xg_col, 'xg_diff']
    ].head(10).copy()

    top_diffs['shot_statsbomb_xg'] = top_diffs['shot_statsbomb_xg'].round(3)
    top_diffs[selected_xg_col] = top_diffs[selected_xg_col].round(3)
    top_diffs['xg_diff'] = top_diffs['xg_diff'].round(3)

    top_diffs.columns = ['Minuta', 'Zawodnik', 'Drużyna', 'Wynik Strzału', 'xG (StatsBomb)', 'xG (Autorskie)', 'Bezwzględna Różnica']
    
    st.dataframe(top_diffs, use_container_width=True, hide_index=True)