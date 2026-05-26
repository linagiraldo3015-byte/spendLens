import streamlit as st

from database.db import init_db
from views import upload, transactions, gmail_import

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
    options=["Registrar gasto", "Importar desde Gmail", "Transacciones"],
)

if pagina == "Registrar gasto":
    upload.render()
elif pagina == "Importar desde Gmail":
    gmail_import.render()
elif pagina == "Transacciones":
    transactions.render()
