import pandas as pd
import streamlit as st

from database.db import get_all_transactions


def render() -> None:
    st.header("Transacciones")

    transactions = get_all_transactions()

    if not transactions:
        st.info("No hay transacciones registradas. Ve a 'Registrar gasto' para agregar una.")
        return

    df = pd.DataFrame(transactions)

    col1, col2, col3 = st.columns(3)
    with col1:
        total = df["monto"].sum()
        st.metric("Total gastos", f"${total:,.0f}")
    with col2:
        st.metric("Transacciones", len(df))
    with col3:
        promedio = df["monto"].mean()
        st.metric("Promedio", f"${promedio:,.0f}")

    st.divider()

    columnas_visibles = {
        "fecha": "Fecha",
        "tipo": "Tipo",
        "monto": "Monto",
        "comercio": "Comercio",
        "contraparte": "Contraparte",
        "direccion": "Direccion",
        "concepto": "Concepto",
        "categoria_nombre": "Categoria",
        "descripcion": "Descripcion",
    }

    df_display = df[[c for c in columnas_visibles if c in df.columns]].copy()
    df_display.rename(columns=columnas_visibles, inplace=True)
    df_display["Monto"] = df_display["Monto"].apply(lambda x: f"${x:,.0f}")

    st.dataframe(df_display, use_container_width=True, hide_index=True)
