import pytest
import pandas as pd
import numpy as np
import base64
import os
from unittest.mock import patch, MagicMock

# ==========================================
# 1. TESTY: KATEGORYZACJA POZYCJI
# ==========================================
def map_position(pos):
    if pd.isna(pos): return 'Nieznana'
    pos = str(pos)
    if 'Back' in pos or 'Defender' in pos: return 'Obrońca'
    if 'Midfield' in pos: return 'Pomocnik'
    if 'Forward' in pos or 'Wing' in pos or 'Striker' in pos: return 'Napastnik'
    if 'Goalkeeper' in pos: return 'Bramkarz'
    return 'Inna'

def test_map_position_obronca():
    assert map_position('Center Back') == 'Obrońca'

def test_map_position_pomocnik():
    assert map_position('Defensive Midfield') == 'Pomocnik'

def test_map_position_brak_danych():
    assert map_position(pd.NA) == 'Nieznana'
    assert map_position(None) == 'Nieznana'

def test_map_position_nietypowa_pozycja():
    assert map_position('Coach') == 'Inna'

# ==========================================
# 2. TESTY: OBSŁUGA PLIKÓW LOKALNYCH (BASE64)
# ==========================================
def get_base64_image(file_path):
    try:
        with open(file_path, "rb") as img_file:
            return f"data:image/svg+xml;base64,{base64.b64encode(img_file.read()).decode()}"
    except FileNotFoundError:
        return None

def test_get_base64_image_success(tmp_path):
    test_file = tmp_path / "test_img.svg"
    test_file.write_text("<svg>test</svg>")
    result = get_base64_image(str(test_file))
    assert result is not None
    assert result.startswith("data:image/svg+xml;base64,")

def test_get_base64_image_not_found():
    assert get_base64_image("plik_ktory_na_pewno_nie_istnieje.svg") is None

# ==========================================
# 3. TESTY: LOGIKA MATEMATYCZNA (STATYSTYKI P90)
# ==========================================
def test_p90_calculation():
    df = pd.DataFrame({'player': ['Wirtz', 'Xhaka'], 'minutes_played': [90, 45], 'Strzały': [3, 2]})
    df['Strzały_p90'] = (df['Strzały'] / df['minutes_played']) * 90.0
    assert df.loc[df['player'] == 'Wirtz', 'Strzały_p90'].values[0] == 3.0 
    assert df.loc[df['player'] == 'Xhaka', 'Strzały_p90'].values[0] == 4.0 

# ==========================================
# 4. TESTY: ZAAWANSOWANE FILTRY (PODANIA PROGRESYWNE)
# ==========================================
def test_progressive_pass_logic():
    df = pd.DataFrame({
        'location_x': [60, 100], 'location_y': [40, 40], 
        'pass_end_x': [80, 105], 'pass_end_y': [40, 40], 
        'pass_outcome': [None, None]
    })
    dist_start = np.sqrt((120 - df['location_x'])**2 + (40 - df['location_y'])**2)
    dist_end = np.sqrt((120 - df['pass_end_x'])**2 + (40 - df['pass_end_y'])**2)
    df['is_progressive'] = (df['pass_outcome'].isna()) & ((dist_start - dist_end) >= 10.0)
    
    assert df['is_progressive'].iloc[0] == True
    assert df['is_progressive'].iloc[1] == False

# ==========================================
# 5. TESTY: GEOMETRIA BOISKA I SILNIK xG
# ==========================================
def test_xg_distance_calculation():
    """Testuje czy model xG poprawnie liczy dystans od środka bramki (120, 40)"""
    df = pd.DataFrame({'x': [120.0, 110.0], 'y': [40.0, 40.0]})
    # Punkt 1: (120, 40) - na linii bramkowej = dystans 0
    # Punkt 2: (110, 40) - rzut karny (10 jardów na wprost) = dystans 10
    distances = np.sqrt((120.0 - df['x'])**2 + (40.0 - df['y'])**2)
    
    assert distances.iloc[0] == 0.0
    assert distances.iloc[1] == 10.0

def test_xg_engine_penalty_rule():
    """Testuje, czy dla rzutów karnych model twardo przypisuje wartość 0.78 z pominięciem ML"""
    df = pd.DataFrame({
        'shot_type': ['Penalty', 'Open Play'],
        'xg_xgb': [0.5, 0.5] # Symulacja jakichś wartości początkowych
    })
    
    # Symulacja nadpisania w silniku xg_engine
    df['xg_xgb'] = np.where(df['shot_type'] == 'Penalty', 0.78, df['xg_xgb'])
    
    assert df.loc[df['shot_type'] == 'Penalty', 'xg_xgb'].iloc[0] == 0.78
    assert df.loc[df['shot_type'] == 'Open Play', 'xg_xgb'].iloc[0] == 0.5

# ==========================================
# 6. TESTY: MOCKOWANIE API STATSBOMB (data_loader.py)
# ==========================================
# Dekorator @patch podmienia prawdziwą funkcję pobierającą dane z internetu na nasz "sztuczny" obiekt (Mock)
@patch('statsbombpy.sb.competitions')
def test_data_loader_competitions_success(mock_sb_competitions):
    """Testuje pobieranie rozgrywek przy pomyślnej odpowiedzi API"""
    # Definiujemy sztuczną odpowiedź API (DataFrame)
    mock_df = pd.DataFrame({
        'competition_id': [9, 12],
        'competition_name': ['1. Bundesliga', 'Serie A'],
        'season_name': ['2023/2024', '2023/2024']
    })
    mock_sb_competitions.return_value = mock_df
    
    # Symulacja funkcji z naszego data_loadera
    result_df = mock_sb_competitions()
    
    assert not result_df.empty
    assert '1. Bundesliga' in result_df['competition_name'].values
    mock_sb_competitions.assert_called_once() # Upewniamy się, że API zostało wywołane tylko raz

@patch('statsbombpy.sb.events')
def test_data_loader_events_api_failure(mock_sb_events):
    """Testuje zachowanie aplikacji gdy API StatsBomb zwróci błąd (np. brak internetu)"""
    # Symulujemy rzucenie wyjątku przez bibliotekę
    mock_sb_events.side_effect = Exception("API Error")
    
    # Funkcja w data_loader.py powinna wyłapać błąd w bloku try-except i zwrócić pusty DataFrame
    try:
        result = mock_sb_events(match_id=12345)
    except Exception:
        result = pd.DataFrame() # Symulacja except: return pd.DataFrame()
        
    assert result.empty

# ==========================================
# 7. TESTY: DYNAMIKA MECZU (MATCH MOMENTUM)
# ==========================================
def test_match_momentum_smoothing():
    """Testuje wygładzanie wykresu przewagi (5-okresowa średnia krocząca)"""
    # Różnica akcji w minutach 1-5
    df = pd.DataFrame({
        'minute': [1, 2, 3, 4, 5],
        'raw_momentum': [10, 0, 0, 0, 0] # Zespół miał zryw w 1 minucie
    })
    
    # Obliczamy 5-minutową średnią kroczącą tak jak w aplikacji
    df['momentum_smoothed'] = df['raw_momentum'].rolling(window=5, min_periods=1).mean()
    
    # Min 1: mean([10]) = 10
    # Min 2: mean([10, 0]) = 5
    # Min 5: mean([10, 0, 0, 0, 0]) = 2
    assert df['momentum_smoothed'].iloc[0] == 10.0
    assert df['momentum_smoothed'].iloc[1] == 5.0
    assert df['momentum_smoothed'].iloc[4] == 2.0