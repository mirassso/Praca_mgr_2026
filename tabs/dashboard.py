import streamlit as st
import pandas as pd
import plotly.express as px

def render(events, ginf):
    st.title("📊 Football Analytics Dashboard")

    # --- 1. PANEL STEROWANIA (Zamiast Sidebaru) ---
    st.markdown("### 🎛️ Filtry analizy")
    
    # Tworzymy 3 kolumny dla filtrów, żeby nie zajmowały dużo miejsca na wysokość
    f_col1, f_col2, f_col3 = st.columns(3)
    
    # Wybór Ligi
    leagues = sorted(ginf['league'].unique())
    selected_league = f_col1.selectbox("Wybierz ligę:", ["Wszystkie"] + leagues)
    
    # Wybór Sezonu
    seasons = sorted(ginf['season_label'].unique())
    selected_season = f_col2.selectbox("Wybierz sezon:", ["Wszystkie"] + seasons)

    # Wstępne filtrowanie ginf dla listy klubów
    temp_ginf = ginf.copy()
    if selected_league != "Wszystkie":
        temp_ginf = temp_ginf[temp_ginf['league'] == selected_league]
    if selected_season != "Wszystkie":
        temp_ginf = temp_ginf[temp_ginf['season_label'] == selected_season]

    # Wybór Klubu
    all_clubs = sorted(pd.concat([temp_ginf['ht'], temp_ginf['at']]).unique())
    selected_club = f_col3.selectbox("Wybierz klub:", ["Wszystkie"] + all_clubs)

    # Ostateczne filtrowanie meczów (ginf)
    filtered_ginf = temp_ginf.copy()
    if selected_club != "Wszystkie":
        filtered_ginf = filtered_ginf[(filtered_ginf['ht'] == selected_club) | (filtered_ginf['at'] == selected_club)]

    # Filtrowanie zdarzeń (events)
    filtered_events = events[events['id_odsp'].isin(filtered_ginf['id_odsp'])]

    st.markdown("---")

    # --- 3. WIZUALIZACJE ---
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Rozkład zdarzeń")
        # Jeśli wybrano klub, ograniczamy koło tylko do jego akcji
        plot_events = filtered_events
        if selected_club != "Wszystkie":
            plot_events = filtered_events[filtered_events['event_team'] == selected_club]
            
        event_counts = plot_events['event_type_name'].value_counts().reset_index()
        event_counts.columns = ['Zdarzenie', 'Liczba']
        fig_events = px.pie(event_counts, values='Liczba', names='Zdarzenie', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_events.update_layout(showlegend=False)
        st.plotly_chart(fig_events, use_container_width=True)

    with c2:
        st.markdown("#### Kiedy padają bramki? (Interwały 10 min)")
        # Filtrujemy tylko gole
        goals_df = filtered_events[filtered_events['is_goal'] == 1]
        if selected_club != "Wszystkie":
            goals_df = goals_df[goals_df['event_team'] == selected_club]
            
        # Histogram z ujednoliconym binningiem (10-minutowe okna)
        fig_time = px.histogram(
            goals_df, 
            x='time', 
            nbins=10, 
            range_x=[0, 100],
            labels={'time': 'Minuta meczu', 'count': 'Liczba goli'},
            color_discrete_sequence=['#2b8a3e']
        )
        # Wymuszamy etykiety osi X co 10 minut
        fig_time.update_layout(
            bargap=0.1,
            xaxis=dict(tickmode='linear', tick0=0, dtick=10)
        )
        st.plotly_chart(fig_time, use_container_width=True)

    # --- 4. ANALIZA DODATKOWA (jeśli wybrano klub) ---
    if selected_club != "Wszystkie":
        st.markdown(f"#### Statystyki dyscyplinarne: {selected_club}")
        cards = filtered_events[
            (filtered_events['event_team'] == selected_club) & 
            (filtered_events['event_type_name'].str.contains('card', na=False, case=False))
        ]
        if not cards.empty:
            card_counts = cards['event_type_name'].value_counts().reset_index()
            card_counts.columns = ['Kartka', 'Ilość']
            st.bar_chart(card_counts.set_index('Kartka'))
        else:
            st.info("Brak zarejestrowanych kartek dla tej drużyny w wybranym okresie.")