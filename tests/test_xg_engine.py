import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import xg_engine

@pytest.fixture
def sample_shots_df():
    return pd.DataFrame({
        'match_id': [1, 1], 'id': ['s1', 's2'], 'type': ['Shot', 'Shot'],
        'shot_type': ['Open Play', 'Free Kick'],
        'location': [[100.0, 40.0], [90.0, 30.0]],
        'shot_body_part': ['Right Foot', 'Head']
    })

@patch('joblib.load')
def test_calculate_custom_xg(mock_joblib_load, sample_shots_df):
    # Tworzymy fałszywy model ML
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.55, 0.45], [0.55, 0.45]])
    mock_joblib_load.return_value = mock_model

    # Uruchamiamy testowaną funkcję
    result_df = xg_engine.calculate_custom_xg(sample_shots_df)
    
    assert not result_df.empty
    assert 'xg_lr' in result_df.columns
    assert 'xg_rf' in result_df.columns
    assert 'xg_xgb' in result_df.columns
    assert np.isclose(result_df['xg_xgb'].iloc[0], 0.45) # Sprawdza czy przepisał wartość z mocka