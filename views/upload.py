import sqlite3
from datetime import date

import streamlit as st

from database.db import get_categorias, insert_categoria, insert_transaction


def render() -> None:
    st.header("Registrar gasto manual")

    tipo = st.radio(
        "Tipo de transaccion",
        options=["compra", "transferencia"],
        horizontal=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        monto = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.0f")
        fecha = st.date_input("Fecha", value=date.today())

    with col2:
        direccion = st.selectbox("Direccion", options=["salida", "entrada"])
        categorias = get_categorias()
        categoria_opciones = ["(Sin categoria)"] + [c["nombre"] for c in categorias]
        categoria_seleccion = st.selectbox("Categoria", options=categoria_opciones)

    if tipo == "compra":
        comercio = st.text_input("Comercio")
        contraparte = None
    else:
        contraparte = st.text_input("Contraparte (persona)")
        comercio = None

    concepto = st.text_input("Concepto (opcional)")
    descripcion = st.text_area("Descripcion (opcional)", height=80)

    st.divider()

    with st.expander("Crear nueva categoria"):
        nueva_cat = st.text_input("Nombre de la nueva categoria", key="nueva_cat")
        if st.button("Agregar categoria"):
            if nueva_cat.strip():
                try:
                    insert_categoria(nueva_cat.strip())
                except sqlite3.IntegrityError:
                    st.error("Esta categoria ya existe.")
                else:
                    st.success(f"Categoria '{nueva_cat.strip()}' creada.")
                    st.rerun()
            else:
                st.warning("Escribe un nombre para la categoria.")

    st.divider()

    if st.button("Guardar transaccion", type="primary"):
        if monto <= 0:
            st.error("El monto debe ser mayor a cero.")
            return

        categoria_id = None
        if categoria_seleccion != "(Sin categoria)":
            categoria_id = next(
                c["id"] for c in categorias if c["nombre"] == categoria_seleccion
            )

        insert_transaction(
            tipo=tipo,
            monto=monto,
            fecha=fecha,
            descripcion=descripcion.strip() or None,
            comercio=comercio.strip() if comercio else None,
            contraparte=contraparte.strip() if contraparte else None,
            direccion=direccion,
            concepto=concepto.strip() or None,
            categoria_id=categoria_id,
        )
        st.success(f"Transaccion guardada: ${monto:,.0f} en {comercio or contraparte or tipo}")
