import streamlit as st

PAGES = [
    st.Page("./pages/upload_files.py", title="Upload to MinIO", icon='📤'),
    st.Page("./pages/gym.py", title="Gym series", icon='🏋️‍♂️'),
    st.Page("./pages/running.py", title="Running sesions", icon='👟'),
    # st.Page("./pages/daily_food.py", title="Macros controller", icon='🍙'),
    # st.Page("./pages/weekly_food.py", title="Weekly menu", icon='🥗')
]

pg = st.navigation(PAGES)
st.set_page_config(
    page_title="Datawarehouse-Salud inputs",  # Esto se verá en la pestaña del navegador
    page_icon="🖋️",
)
pg.run()