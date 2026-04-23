import streamlit as st
import pandas as pd
import plotly.express as px

def render(events, ginf):
    st.title("👥 Analiza zawodników")

    goals = events[events['is_goal'] == 1]
    player_stats = goals['player'].value_counts().reset_index().head(20)
    player_stats.columns = ['Zawodnik', 'Gole']

    fig = px.bar(player_stats, x='Zawodnik', y='Gole', title="Najskuteczniejsi zawodnicy")
    st.plotly_chart(fig, use_container_width=True)
