import streamlit as st
import pandas as pd
import os

##### PREAMBLE #####
SHEETS = ['Push1', 'Pull1', 'Push2', 'Pull2', 'Temporal']
COLS = ['fecha', 'num', 'ejercicio', 'peso', 'reps', 'RIR', 'RPE']
CSV_FILE = "data/series_gimnasio.csv"
VALIDATION = []

def read_excel_data(excelFile):
    df_list = []
    for sheet in SHEETS:
        df_gym = pd.read_excel(io=excelFile, sheet_name=sheet, parse_dates=['fecha'])
        df_gym = df_gym[df_gym["Validez"].str.strip() == "Valido"]
        df_gym = df_gym[COLS]
        df_list.append(df_gym)
    return pd.concat(df_list, ignore_index=True)

##### RENDERED CODE #####

# Load initial data
if 'df_gym' not in st.session_state:    
    if os.path.exists(CSV_FILE):
        st.session_state.df_gym = pd.read_csv(CSV_FILE, parse_dates=['fecha'])
    else:
        raise RuntimeError(f"No file {CSV_FILE} found")

# Title visual
st.set_page_config(layout="wide")
st.title("Gym series 🏋️‍♂️")

with st.container(horizontal=True):
    cols = st.columns(3)
    with cols[0]:
        # File uploader visual: upload excel file to extract data from
        uploaded_file = st.file_uploader('Load from Excel', 'xlsx', accept_multiple_files=False)
        if uploaded_file is not None:
            df_gym = st.session_state.df_gym
            df_xlsx = read_excel_data(uploaded_file)
            df_gym = pd.concat([df_gym, df_xlsx], ignore_index=True)
            df_gym = df_gym.drop_duplicates()
            st.session_state.df_gym = df_gym

# Dataframe visual: present df data
st.subheader("Current data")
st.dataframe(st.session_state.df_gym.sort_values(by=['fecha', 'num'], ascending=True))

# Button visual: save data as CSV
if st.button("Save changes as CSV"):
    df_gym = st.session_state.df_gym.sort_values(by=['fecha', 'num'], ascending=True)
    df_gym.drop_duplicates()
    df_gym.to_csv(CSV_FILE, index=False, encoding="UTF-8")
    st.success(f"Data saved correctly in {CSV_FILE}")