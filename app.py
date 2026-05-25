import streamlit as st

from database.db import init_db
from views import upload, transactions

st.set_page_config(
    page_title="SpendLens",
    page_icon="$",
    layout="wide",
)


@st.cache_resource
def setup_database() -> None:
    init_db()


setup_database()

st.sidebar.title("SpendLens")
st.sidebar.caption("Seguimiento inteligente de gastos personales")

pagina = st.sidebar.radio(
    "Navegacion",
    options=["Registrar gasto", "Transacciones"],
)

if pagina == "Registrar gasto":
    upload.render()
elif pagina == "Transacciones":
    transactions.render()
