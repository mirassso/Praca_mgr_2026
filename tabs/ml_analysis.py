import streamlit as st
import pandas as pd

def render(events, ginf):
    st.title("📈 Analiza modeli ML")

    st.write("Tu możesz pokazać porównanie modeli, ich metryki, ROC curve itp.")
    data = {
        "Model": ["Logistic Regression", "Random Forest", "LightGBM"],
        "AUC": [0.72, 0.78, 0.81],
        "Accuracy": [0.68, 0.74, 0.77]
    }
    st.dataframe(pd.DataFrame(data))
