import streamlit as st
import pandas as pd
import os

CSV_FILE = "data/menu_semanal.csv"
CSV_DTYPES = {'Franja': 'string','Plato': 'string','Cantidad': 'Int32','Tiempo': 'Int32'}
DISHES_INFO_CSV = 'data/informacion_nutricional.csv'
DISHES_NAMES = list(pd.read_csv(DISHES_INFO_CSV)['nombre_plato'])
SLOTS_OPTIONS = ["Desayuno", "Comida", "Cena"]
CATEGORY_OPTIONS = ["Primero", "Segundo", "Plato único", "Guarnición"]

# Load initial data
if not (os.path.exists(CSV_FILE) and os.path.exists(DISHES_INFO_CSV)):
    raise RuntimeError(f"No file {CSV_FILE} found")

##### RENDERED CODE #####
# Page config
st.set_page_config(layout="wide")

# Title visual
st.title("Weekly food plan 🥗")

# Button visual: save data as CSV
if st.button("Save data in CSV"):
    if 'edited_df_daily_menu' in st.session_state:
        df_completo = pd.read_csv(CSV_FILE, dtype=CSV_DTYPES, parse_dates=['Fecha'], date_format='%Y-%m-%d')
        df_completo[df_completo['Fecha'] == st.session_state.selected_day] = st.session_state.edited_df_daily_menu.values
        df_completo.to_csv(CSV_FILE, index=False, encoding='utf-8')
        st.success(f"Data saved in {CSV_FILE} correctly")
    else:
        st.warning("There are no changes yet")

# Container visual: user inputs gathering
with st.container():
    input_widgets = st.columns(4)
    
    with input_widgets[0]:
        # Date input visual: selected day for analysis
        default_value = 'today' if 'selected_day' not in st.session_state else st.session_state.selected_day
        selected_day = st.date_input('Día', 'today')
        selected_day = pd.to_datetime(selected_day)
        st.session_state.selected_day = selected_day
    with input_widgets[1]:
        # Number input visual: burned calories selector
        burned_calories = st.number_input('Calorías consumidas', icon='🔥', min_value=0, step=1, value=400)
    with input_widgets[2]:
        # Slider visual: weigth selector
        weight = st.slider('Peso', min_value=0.0, max_value=120.0, value=80.0, step=0.1)

# Data editor visual: edit df data
st.subheader("Current data")

df_daily_menu = pd.read_csv(CSV_FILE, dtype=CSV_DTYPES, parse_dates=['Fecha'], date_format='%Y-%m-%d')
df_daily_menu = df_daily_menu[df_daily_menu['Fecha'] == selected_day]

df_menu_info = pd.read_csv(DISHES_INFO_CSV, usecols=['nombre_plato', 'cals', 'proteinas', 'grasas', 'carbohidratos'])

edited_df_daily_menu = st.data_editor(
    df_daily_menu,
    num_rows="dynamic",
    width='stretch',
    column_config={
        "Fecha": st.column_config.DateColumn(
            "Fecha",
            required=True,
        ),
        "Franja": st.column_config.SelectboxColumn(
            "Franja",
            options=SLOTS_OPTIONS,
            required=True
        ),
        "Plato": st.column_config.SelectboxColumn(
            "Plato",
            required=True,
            options=DISHES_NAMES
        ),
        "Cantidad": st.column_config.NumberColumn(
            "Cantidad",
            required=True,
            min_value=0,
        ),
        "Tiempo": st.column_config.NumberColumn(
            "Tiempo",
            required=False,
            min_value=0,
        )
    }
)
st.session_state.edited_df_daily_menu = edited_df_daily_menu

menu_with_info = pd.merge(edited_df_daily_menu, df_menu_info, how='left', right_on='nombre_plato', left_on='Plato')

# Metrics visual: show macro information based on your menu
with st.container(border=True, horizontal_alignment='right'):
    macros = st.columns(4)
    
    calories = (menu_with_info['cals'] * menu_with_info['Cantidad'] / 100).sum()
    maintenance_calories = ((10 * weight) + (6.25 * 174) - (5 * 23) + 5)
    proteinas = (menu_with_info['proteinas'] * menu_with_info['Cantidad'] / 100).sum()
    grasas = (menu_with_info['grasas'] * menu_with_info['Cantidad'] / 100).sum()
    carbohidratos = (menu_with_info['carbohidratos'] * menu_with_info['Cantidad'] / 100).sum()

    with macros[0]:
        st.metric('Calorías 🔥', f'{calories:.2f}', calories - burned_calories - maintenance_calories, 'inverse')
    with macros[1]:
        st.metric('Proteínas 🔴', f'{proteinas:.2f}')
    with macros[2]:
        st.metric('Grasas 🟠', f'{grasas:.2f}')
    with macros[3]:
        st.metric('Carbohidratos 🟡', f'{carbohidratos:.2f}')