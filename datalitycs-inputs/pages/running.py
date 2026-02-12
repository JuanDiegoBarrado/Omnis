import streamlit as st
from datetime import date
import pandas as pd
from typing import Any, cast
import os

CSV_FILE = "data/sesiones_carrera.csv"
CSV_DTYPES: dict[str, str] = {'Num': 'Int32','Categoria': 'string','Modalidad': 'string','Distancia': 'float32','Tiempo': 'string','Cals': 'Int32','FCavg': 'Int32','FCmax': 'Int32','por_Z1': 'Int32','por_Z2': 'Int32','por_Z3': 'Int32','por_Z4': 'Int32','por_Z5': 'Int32'}
CATEGORIA_VALIDATION = ["Easy run", "Long run", "Tempo", "Intervals", "Fartlek", "Hills", "Recovery"]
MODALIDAD_VALIDATION = ["Correr en cinta", "Correr al aire libre", "Caminar en cinta", "Caminar al aire libre", "Caminata"]

# Load initial data
if 'df_running' not in st.session_state:    
    if os.path.exists(CSV_FILE):
        st.session_state.df_running = pd.read_csv(CSV_FILE, dtype=cast(Any, CSV_DTYPES), parse_dates=['Fecha'], date_format='%Y-%m-%d')
        st.session_state.df_running['Fecha'] = pd.to_datetime(st.session_state.df_running['Fecha'], format='%Y-%m-%d', errors='coerce')
    else:
        raise RuntimeError(f"No file {CSV_FILE} found")
    
##### RENDERED CODE #####
# Page config
st.set_page_config(
    page_title="Running",
    page_icon="👟",
)

# Title visual
st.title("Running sessions 👟")

# Data editor visual: edit df data
st.subheader("Current data")
edited_df = st.data_editor(
    st.session_state.df_running,
    num_rows="dynamic",
    width='stretch',
    column_config={
        "Fecha": st.column_config.DateColumn(
            "Fecha",
            default=date.today(),
            required=True
        ),
        "Num": st.column_config.NumberColumn(
            "Num",
            required=True
        ),
        "Categoria": st.column_config.SelectboxColumn(
            "Categoria",
            options=CATEGORIA_VALIDATION,
            required=True
        ),
        "Modalidad": st.column_config.SelectboxColumn(
            "Modalidad",
            options=MODALIDAD_VALIDATION,
            required=True
        ),
        "Distancia": st.column_config.NumberColumn(
            "Distancia",
            min_value=0.0,
            max_value=1000.0,
            step=0.01,
            format="%.2f",
            required=True
        ),
        "Tiempo": st.column_config.TextColumn(
            "Tiempo",
            required=True,
            validate=r"^([0-1]\d|2[0-3]):([0-5]\d):([0-5]\d)$"
        ),
        "Cals": st.column_config.NumberColumn(
            "Cals",
            required=True,
            min_value=0,
            max_value=10000,
        ),
        "FCavg": st.column_config.NumberColumn(
            "FCavg",
            required=True,
            min_value=0,
            max_value=10000,
        ),
        "FCmax": st.column_config.NumberColumn(
            "FCmax",
            required=True,
            min_value=0,
            max_value=10000,
        ),
        "por_Z1": st.column_config.NumberColumn(
            "por_Z1",
            required=True,
            min_value=0,
            max_value=1440
        ),
        "por_Z2": st.column_config.NumberColumn(
            "por_Z2",
            required=True,
            min_value=0,
            max_value=1440
        ),
        "por_Z3": st.column_config.NumberColumn(
            "por_Z3",
            required=True,
            min_value=0,
            max_value=1440
        ),
        "por_Z4": st.column_config.NumberColumn(
            "por_Z4",
            required=True,
            min_value=0,
            max_value=1440
        ),
        "por_Z5": st.column_config.NumberColumn(
            "por_Z5",
            required=True,
            min_value=0,
            max_value=1440
        )
    }
)
st.session_state.df_running = edited_df

# Button visual: save data as CSV
if st.button("Save changes as CSV"):
    st.session_state.df_running.to_csv(CSV_FILE, index=False, encoding='utf-8')
    st.success(f"Data saved in {CSV_FILE} correctly")