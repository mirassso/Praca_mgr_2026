import pandas as pd
import numpy as np
import joblib
import streamlit as st
import ast
import json

def load_xg_models():
    try:
        lr_model = joblib.load('models/xg_logreg.joblib')
        rf_model = joblib.load('models/xg_rf_tuned.joblib')
        xgb_model = joblib.load('models/xg_xgboost.joblib')
        expected_columns = joblib.load('models/xg_columns.joblib')
        return lr_model, rf_model, xgb_model, expected_columns
    except Exception as e:
        return None, None, None, None

def get_freeze_frame_features(row):
    frame = row.get('shot_freeze_frame', [])
    
    if isinstance(frame, float) and pd.isna(frame):
        frame = []
    elif isinstance(frame, str):
        try: frame = ast.literal_eval(frame)
        except: 
            try: frame = json.loads(frame.replace("'", '"'))
            except: frame = []
            
    if not isinstance(frame, list):
        frame = []
        
    shooter_x = row.get('x', 120.0)
    shooter_y = row.get('y', 40.0)
    
    if len(frame) == 0:
        sb_xg = row.get('shot_statsbomb_xg', row.get('xG (StatsBomb)', 0.0))
        try: sb_xg = float(sb_xg)
        except: sb_xg = 0.0
        dist = np.sqrt((120.0 - shooter_x)**2 + (40.0 - shooter_y)**2)
        
        if sb_xg > 0.50 and dist < 25.0:
            return pd.Series([5.0, 30.0, 0, 0]) 
        else:
            return pd.Series([0.0, 5.0, 2, 2])

    gk_x, gk_y = 120.0, 40.0
    closest_def_dist = 30.0
    defs_in_cone = 0
    defs_in_front = 0
    
    for p in frame:
        if not p.get('teammate', True):
            loc = p.get('location', [120.0, 40.0])
            if p.get('position', {}).get('name') == 'Goalkeeper':
                gk_x, gk_y = loc[0], loc[1]
            else:
                dx, dy = loc[0], loc[1]
                dist = np.sqrt((shooter_x - dx)**2 + (shooter_y - dy)**2)
                if dist < closest_def_dist:
                    closest_def_dist = dist
                
                # Zliczanie obrońców przed piłką
                if dx >= (shooter_x - 0.5):
                    defs_in_front += 1
                
                if dx > shooter_x:
                    t = (dx - shooter_x) / max(0.1, 120.0 - shooter_x)
                    upper_y = shooter_y + t * (44.0 - shooter_y) + 1.0
                    lower_y = shooter_y + t * (36.0 - shooter_y) - 1.0
                    if lower_y <= dy <= upper_y:
                        defs_in_cone += 1
                        
    gk_dist_from_goal = np.sqrt((120.0 - gk_x)**2 + (40.0 - gk_y)**2)
    return pd.Series([gk_dist_from_goal, closest_def_dist, defs_in_cone, defs_in_front])

def calculate_custom_xg(shots_df):
    if shots_df.empty: return shots_df

    lr_model, rf_model, xgb_model, expected_columns = load_xg_models()
    if lr_model is None:
        shots_df['autorskie_xg'] = np.nan
        return shots_df

    df = shots_df.copy()

    if 'location' in df.columns:
        df['x'] = df['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else np.nan)
        df['y'] = df['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else np.nan)
    else:
        df['x'] = df.get('location_x', 120.0)
        df['y'] = df.get('location_y', 40.0)

    df['distance_to_goal'] = np.sqrt((120.0 - df['x'])**2 + (40.0 - df['y'])**2)
    
    a = np.sqrt((120.0 - df['x'])**2 + (36.0 - df['y'])**2)
    b = np.sqrt((120.0 - df['x'])**2 + (44.0 - df['y'])**2)
    with np.errstate(divide='ignore', invalid='ignore'):
        cos_angle = (a**2 + b**2 - 64.0) / (2 * a * b)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        df['shot_angle'] = np.arccos(cos_angle)
    df['shot_angle'] = df['shot_angle'].fillna(0)

    df[['gk_dist_from_goal', 'closest_def_dist', 'defs_in_cone', 'defs_in_front']] = df.apply(get_freeze_frame_features, axis=1)
    
    # Przenosimy flagę breakway
    df['is_breakaway'] = (df['defs_in_front'] == 0).astype(int)

    df['is_penalty'] = (df.get('shot_type', '') == 'Penalty').astype(int)
    df['is_first_time'] = df.get('shot_first_time', pd.Series(False, index=df.index)).fillna(False).astype(int)

    if 'shot_body_part' in df.columns:
        df['shot_body_part_Left Foot'] = (df['shot_body_part'] == 'Left Foot').astype(int)
        df['shot_body_part_Right Foot'] = (df['shot_body_part'] == 'Right Foot').astype(int)
        df['shot_body_part_Other'] = (~df['shot_body_part'].isin(['Left Foot', 'Right Foot'])).astype(int)
        df['shot_body_part_Left_Foot'] = df['shot_body_part_Left Foot']
        df['shot_body_part_Right_Foot'] = df['shot_body_part_Right Foot']
    else:
        df['shot_body_part_Left Foot'], df['shot_body_part_Right Foot'], df['shot_body_part_Other'] = 0, 0, 1
        df['shot_body_part_Left_Foot'], df['shot_body_part_Right_Foot'] = 0, 0

    X_predict = pd.DataFrame()
    for col in expected_columns:
        if col in df.columns: X_predict[col] = df[col]
        elif col.replace('_', ' ') in df.columns: X_predict[col] = df[col.replace('_', ' ')]
        elif col.replace(' ', '_') in df.columns: X_predict[col] = df[col.replace(' ', '_')]
        else: X_predict[col] = 0.0

    shots_df['xg_lr'] = lr_model.predict_proba(X_predict)[:, 1]
    shots_df['xg_rf'] = rf_model.predict_proba(X_predict)[:, 1]
    shots_df['xg_xgb'] = xgb_model.predict_proba(X_predict)[:, 1]
    
    shots_df['autorskie_xg'] = shots_df['xg_xgb']
    
    return shots_df