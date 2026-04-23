import streamlit as st
import joblib
import os

def render(events, ginf):
    st.title("🧠 Model Expected Goals (xG)")

    model_path = "models/xg_model.joblib"

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        st.success("✅ Model załadowany poprawnie.")
    else:
        st.warning("⚠️ Model jeszcze nie został wytrenowany i zapisany. Użyj notebooka do treningu.")

    st.markdown("### Predykcja przykładowego strzału (po integracji modelu)")
