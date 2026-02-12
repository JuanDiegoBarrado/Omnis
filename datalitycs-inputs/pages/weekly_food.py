import streamlit as st
import pandas as pd
import os
import plotly.express as px

CSV_FILE = "data/menu_semanal.csv"
CSV_DTYPES = {'Franja': 'string','Plato': 'string','Cantidad': 'Int32','Tiempo': 'Int32'}
DISHES_INFO_CSV = 'data/informacion_nutricional.csv'
DISHES_NAMES = list(pd.read_csv(DISHES_INFO_CSV)['nombre_plato'])
SLOTS_OPTIONS = ["Desayuno", "Comida", "Cena"]
CATEGORY_OPTIONS = ["Primero", "Segundo", "Plato unico", "Guarnicion"]
TYPE_OPTIONS = ['verdura', 'carne_roja', 'carne_blanca', 'pescado', 'legumbres', 'hidratos_de_carbono']

# Load initial data
if not (os.path.exists(CSV_FILE) and os.path.exists(DISHES_INFO_CSV)):
    raise RuntimeError(f"No file {CSV_FILE} found")

##### RENDERED CODE #####
# Page config
st.set_page_config(layout="wide")

# Title visual
st.title("Weekly food plan 🥗")

with st.container(horizontal=True):
    # Button visual: save data as CSV
    if st.button("Save data in CSV"):
        if 'edited_df_menu' in st.session_state:
            st.session_state.edited_df_menu.to_csv(CSV_FILE, index=False, encoding='utf-8')
            st.success(f"Data saved in {CSV_FILE} correctly")
        else:
            st.warning("There are no changes yet")
            
    # Button visual: export recipes PDF
    if st.button("Prepare download"):
        if 'edited_df_menu' in st.session_state:
            nutritional_info = pd.read_csv(DISHES_INFO_CSV, usecols=['nombre_plato', 'receta'])
            df_recipes = pd.merge(st.session_state.edited_df_menu, nutritional_info, how='left', right_on='nombre_plato', left_on='Plato')
            recipes = "\n\n---\n\n".join(df_recipes['receta'].tolist())
            st.download_button(
                label='Download markdown with recipes',
                data=recipes,
                file_name='Recetas.md',
                mime='text/markdown'
            )
        else:
            st.warning("There are no changes yet")

# Data editor visual: edit df data
st.subheader("Current data")

df_menu = pd.read_csv(CSV_FILE, dtype=CSV_DTYPES, parse_dates=['Fecha'], date_format='%Y-%m-%d')
df_info = pd.read_csv(DISHES_INFO_CSV, usecols=['nombre_plato', 'categoria', 'cals', 'proteinas', 'grasas', 'carbohidratos', 'verdura', 'carne_roja', 'carne_blanca', 'pescado', 'legumbres', 'hidratos_de_carbono'])

edited_df_menu = st.data_editor(
    df_menu,
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
st.session_state.edited_df_menu = edited_df_menu

with st.expander('Dish selector assitant'):
    with st.container(horizontal=True):
        filter1 = st.selectbox('Filter by', TYPE_OPTIONS)
        filter2 = st.selectbox('Filter by', CATEGORY_OPTIONS)

    showable_df = df_info[df_info[filter1] == True]
    showable_df = showable_df[showable_df['categoria'] == filter2]
    showable_df = showable_df[['nombre_plato', 'cals', 'proteinas', 'grasas', 'carbohidratos']]
    st.dataframe(showable_df)

st.subheader('Nutritional information')
df_recipes = pd.merge(edited_df_menu, df_info, how='left', right_on='nombre_plato', left_on='Plato')

with st.container(border=True, horizontal_alignment='distribute'):
    nut_info = st.columns(2, vertical_alignment='center')
    
    with nut_info[0]:
        # Metrics visual: show how good is the menu based on your own metrics
        with st.container(horizontal_alignment='center', vertical_alignment='center'):
            tipos_fila_1 = st.columns(3)

            with tipos_fila_1[0]:
                num_verduras = df_recipes['verdura'].sum()
                total_num_verduras = 5
                st.metric('Verduras 🥦', num_verduras, num_verduras - total_num_verduras)
            with tipos_fila_1[1]:
                num_legumbres = df_recipes['legumbres'].sum()
                total_num_legumbres = 2
                st.metric('Legumbres 🌱', num_legumbres, num_legumbres - total_num_legumbres)
            with tipos_fila_1[2]:
                num_carne_roja = df_recipes['carne_roja'].sum()
                total_num_carne_roja = 2
                st.metric('Carne Roja 🥩', num_carne_roja, num_carne_roja - total_num_carne_roja)
            
            tipos_fila_2 = st.columns(3)
            
            with tipos_fila_2[0]:
                num_carne_blanca = df_recipes['carne_blanca'].sum()
                total_num_carne_blanca = 3
                st.metric('Carne Blanca 🐔', num_carne_blanca, num_carne_blanca - total_num_carne_blanca)
            with tipos_fila_2[1]:
                num_pescado = df_recipes['pescado'].sum()
                total_num_pescado = 5
                st.metric('Pescado 🐟', num_pescado, num_pescado - total_num_pescado)
            with tipos_fila_2[2]:
                num_carbohidratos = df_recipes['hidratos_de_carbono'].sum()
                total_num_carbohidratos = 5
                st.metric('Hidratos de carbono 🍞', num_carbohidratos, num_carbohidratos - total_num_carbohidratos)
    
    with nut_info[1]:
        # Pie chart visual: show macros total distribution
        with st.container(horizontal_alignment='center', vertical_alignment='center'):
            proteinas = (df_recipes['proteinas'] * df_recipes['Cantidad'] / 100).sum()
            grasas = (df_recipes['grasas'] * df_recipes['Cantidad'] / 100).sum()
            carbohidratos = (df_recipes['carbohidratos'] * df_recipes['Cantidad'] / 100).sum()
            
            fig = px.pie(values=[proteinas, grasas, carbohidratos], names=['Proteínas', 'Grasas', 'Carbohidratos'], color_discrete_sequence=['#E74C3C', '#F39C12', '#F4D03F'])
            fig.update_layout(
                width=500,
                height=320
            )
            st.plotly_chart(fig)