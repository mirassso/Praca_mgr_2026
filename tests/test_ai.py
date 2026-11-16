import sys
import os
# Dodajemy główny folder aplikacji do ścieżki Pythona
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, mock_open

# Importujemy testowany moduł
import tabs.ml_reports as ml_module

# ==========================================
# 1. TESTY: INTEGRACJA Z GOOGLE GEMINI API
# ==========================================
@patch('tabs.ml_reports.genai.Client')
def test_generate_gemini_report_success(mock_genai_client):
    """Testuje, czy aplikacja poprawnie odbiera i parsuje JSONa od modelu sztucznej inteligencji."""
    fake_ai_response = """
    ```json
    {
        "profil": "Ofensywny pomocnik.",
        "atuty_i_braki": "Dobre podania, słaby odbiór.",
        "dystrybucja": "Często gra do przodu.",
        "strzaly": "Skuteczny z dystansu.",
        "werdykt": "Kluczowy zawodnik."
    }
    ```
    """
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = fake_ai_response
    mock_client_instance.models.generate_content.return_value = mock_response
    mock_genai_client.return_value = mock_client_instance

    test_payload = {"Typ": "Gracz", "Minuty": 900}
    result = ml_module.generate_gemini_report(
        data_dict=test_payload, 
        report_type="Gracz", 
        entity_name="Test Player", 
        api_key="FAKEY_API_KEY_123"
    )
    
    assert result is not None
    assert type(result) == dict
    assert result["profil"] == "Ofensywny pomocnik."
    assert "werdykt" in result
    mock_client_instance.models.generate_content.assert_called_once()

@patch('tabs.ml_reports.genai.Client')
def test_generate_gemini_report_failure(mock_genai_client):
    """Testuje zachowanie aplikacji, gdy API Google ulegnie awarii."""
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = Exception("Google API Down")
    mock_genai_client.return_value = mock_client_instance
    
    result = ml_module.generate_gemini_report({}, "Gracz", "Test Player", "FAKEY_API_KEY_123")
    assert result is None

# ==========================================
# 2. TESTY: POBIERANIE CZCIONEK Z SIECI
# ==========================================
@patch('tabs.ml_reports.requests.get')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', return_value=False)
def test_download_unicode_fonts(mock_exists, mock_file, mock_get):
    """Testuje łączność z serwerem przy pobieraniu czcionek do PDF."""
    mock_response = MagicMock()
    mock_response.content = b"fake_font_binary_data"
    mock_get.return_value = mock_response

    reg_font, bold_font = ml_module.download_unicode_fonts()

    assert reg_font == "Roboto-Regular.ttf"
    assert bold_font == "Roboto-Bold.ttf"
    assert mock_get.call_count == 2

# ==========================================
# 3. TESTY: BUDOWANIE BAZY SKAUTINGOWEJ
# ==========================================
@patch('tabs.ml_reports.dl.get_match_events')
def test_build_scouting_database(mock_get_events):
    """Testuje agregację danych i poprawność obliczeń bazy graczy."""
    matches_df = pd.DataFrame({
        'match_id': [1, 2],
        'home_team': ['Bayer Leverkusen', 'Bayern Munich'],
        'away_team': ['Borussia', 'Bayer Leverkusen']
    })
    
    events_df = pd.DataFrame({
        'match_id': [1, 1, 1],
        'minute': [10, 45, 95],
        'player': ['Florian Wirtz', 'Florian Wirtz', 'Florian Wirtz'],
        'team': ['Bayer Leverkusen', 'Bayer Leverkusen', 'Bayer Leverkusen'],
        'type': ['Pass', 'Shot', 'Carry'],
        'pass_shot_assist': [True, None, None]
    })
    
    mock_get_events.return_value = events_df

    ml_module.build_scouting_database.clear()
    full_df, stats_df = ml_module.build_scouting_database(matches_df, 'Bayer Leverkusen')

    assert not full_df.empty
    assert not stats_df.empty
    assert 'Florian Wirtz' in stats_df['player'].values
    assert stats_df['minutes_played'].iloc[0] == 95
    
    # POPRAWKA: Pętla idzie przez 2 mecze z tej samej zmockowanej ramki: 1 strzał * 2 = 2
    assert stats_df['Strzały'].iloc[0] == 2
    assert stats_df['Kreatywność'].iloc[0] == 2

# ==========================================
# 4. TESTY: GENERATOR PLIKÓW PDF
# ==========================================
def test_create_pdf_report_no_crash():
    """Weryfikuje układ i binarny eksport pliku PDF."""
    ai_json = {
        "profil": "Ofensywny pomocnik.",
        "atuty_i_braki": "Świetny przegląd pola.",
        "werdykt": "Kluczowy dla zespołu."
    }
    stats_payload = {"Minuty": 950, "Percentyle": {"Strzały": 85, "Kreatywność": 99}}
    
    with patch('tabs.ml_reports.add_pdf_figure_inline', return_value=10):
        pdf_bytes = ml_module.create_pdf_report(
            ai_json=ai_json, 
            entity_name="Florian Wirtz", 
            report_type="Gracz", 
            figures_dict={}, 
            stats_payload=stats_payload
        )
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b'%PDF-')

# ==========================================
# 5. TESTY: RENDEROWANIE INTERFEJSU (UI STREAMLIT)
# ==========================================
@patch('tabs.ml_reports.st')
@patch('tabs.ml_reports.build_scouting_database')
@patch('tabs.ml_reports.generate_gemini_report')
@patch('tabs.ml_reports.create_pdf_report')
def test_render_player_report_ui(mock_create_pdf, mock_generate_gemini, mock_build_db, mock_st):
    """Testuje przejście przez pełną ścieżkę generowania raportu w UI."""
    
    # 1. Tworzymy specjalną klasę udającą st.session_state (obsługuje i kropkę, i słownik)
    class DummySessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    mock_st.session_state = DummySessionState()
    mock_st.secrets = {"GEMINI_API_KEY": "fake_key_123"}
    
    # Symulacja interakcji użytkownika
    mock_st.radio.return_value = "Gracz"
    # ... reszta kodu zostaje bez zmian! ...
    
    # Symulacja interakcji użytkownika
    mock_st.radio.return_value = "Gracz"
    mock_st.selectbox.side_effect = ["Bayer Leverkusen", "Florian Wirtz"]
    mock_st.button.return_value = True 
    mock_st.checkbox.return_value = True
    
    # Zaślepienie funkcji wizualnych
    mock_spinner = MagicMock()
    mock_spinner.__enter__.return_value = None
    mock_spinner.__exit__.return_value = None
    mock_st.spinner.return_value = mock_spinner
    
    mock_st.columns.side_effect = lambda x: [MagicMock()] * (x if isinstance(x, int) else len(x))

    # Symulowane zwroty funkcji
    matches_df = pd.DataFrame({
        'match_id': [1], 'home_team': ['Bayer Leverkusen'], 'away_team': ['Bayern'], 'match_date': ['2023-10-10']
    })
    full_df = pd.DataFrame({
        'match_id': [1], 'player': ['Florian Wirtz'], 'team': ['Bayer Leverkusen'], 
        'type': ['Pass'], 'location_x': [50], 'location_y': [50], 
        'pass_end_x': [60], 'pass_end_y': [60], 'pass_outcome': [None], 'minute': [10]
    })
    stats_df = pd.DataFrame({
        'player': ['Florian Wirtz'], 'minutes_played': [90],
        'Strzały_pct': [90], 'Kreatywność_pct': [85], 'Rozegranie_pct': [80],
        'Prowadzenie Piłki_pct': [70], 'Akcje Defensywne_pct': [40], 'Presja_pct': [50]
    })
    
    mock_build_db.return_value = (full_df, stats_df)
    mock_generate_gemini.return_value = {
        "profil": "Super gracz", "atuty_i_braki": "Brak braków", 
        "dystrybucja": "Genialna", "strzaly": "Mocne", "werdykt": "Kupować"
    }
    mock_create_pdf.return_value = b"%PDF-mock-binary-data"

    # Uruchomienie testu
    ml_module.render(matches_df)
    
    # Asercje potwierdzające wywołanie kluczowych elementów interfejsu
    mock_st.title.assert_called()
    mock_generate_gemini.assert_called_once()
    mock_st.plotly_chart.assert_called()
    mock_st.download_button.assert_called_once()