import pandas as pd
import streamlit as st

from database.db import get_all_transactions

_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def render() -> None:
    st.header("Transacciones")

    transactions = get_all_transactions()
    if not transactions:
        st.info("No hay transacciones registradas. Ve a 'Registrar gasto' para agregar una.")
        return

    df = pd.DataFrame(transactions)
    df["fecha"] = pd.to_datetime(df["fecha"])

    # --- Filtros ---
    col_mes, col_anio, col_cat, col_tipo = st.columns(4)

    with col_mes:
        meses_opciones = ["Todos"] + _MESES
        mes_sel = st.selectbox("Mes", options=meses_opciones)

    with col_anio:
        anios_disponibles = sorted(df["fecha"].dt.year.unique(), reverse=True)
        anios_opciones = ["Todos"] + [str(a) for a in anios_disponibles]
        anio_sel = st.selectbox("Año", options=anios_opciones)

    with col_cat:
        if "categoria_nombre" in df.columns:
            cats = sorted(c for c in df["categoria_nombre"].dropna().unique())
        else:
            cats = []
        cat_opciones = ["Todas"] + cats
        cat_sel = st.selectbox("Categoría", options=cat_opciones)

    with col_tipo:
        tipo_sel = st.selectbox("Tipo", options=["Todos", "compra", "transferencia"])

    # --- Aplicar filtros ---
    df_filtrado = df.copy()

    if mes_sel != "Todos":
        mes_num = _MESES.index(mes_sel) + 1
        df_filtrado = df_filtrado[df_filtrado["fecha"].dt.month == mes_num]

    if anio_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["fecha"].dt.year == int(anio_sel)]

    if cat_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["categoria_nombre"] == cat_sel]

    if tipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_sel]

    st.divider()

    # --- Métricas (sobre el resultado filtrado) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        total = df_filtrado["monto"].sum()
        st.metric("Total gastos", f"${total:,.0f}")
    with col2:
        st.metric("Transacciones", len(df_filtrado))
    with col3:
        promedio = df_filtrado["monto"].mean() if len(df_filtrado) > 0 else 0
        st.metric("Promedio", f"${promedio:,.0f}")

    st.divider()

    if df_filtrado.empty:
        st.info("No hay transacciones que coincidan con los filtros seleccionados.")
        return

    # --- Tabla ---
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
    df_display = df_filtrado[[c for c in columnas_visibles if c in df_filtrado.columns]].copy()
    df_display.rename(columns=columnas_visibles, inplace=True)
    df_display["Fecha"] = df_display["Fecha"].dt.strftime("%Y-%m-%d")
    df_display["Monto"] = df_display["Monto"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(df_display, width="stretch", hide_index=True)