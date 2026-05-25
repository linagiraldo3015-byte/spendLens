import sqlite3
from datetime import date

import streamlit as st

from database.db import get_categorias, insert_categoria, insert_transaction
from ingestion.photo_parser import parse_receipt_image


def render() -> None:
    st.header("Registrar gasto")

    tab_manual, tab_foto = st.tabs(["Entrada manual", "Foto de factura"])

    with tab_manual:
        _render_manual_form()

    with tab_foto:
        _render_photo_upload()


def _render_photo_upload() -> None:
    uploaded = st.file_uploader(
        "Sube una foto de factura o recibo",
        type=["jpg", "jpeg", "png", "webp"],
        key="photo_upload",
    )

    if uploaded is None:
        st.info("Sube una imagen y Claude extraera los datos automaticamente.")
        return

    st.image(uploaded, caption="Imagen subida", width=300)

    if st.button("Extraer datos con IA", type="primary"):
        with st.spinner("Analizando imagen con Claude..."):
            image_data = uploaded.getvalue()
            media_type = f"image/{uploaded.type.split('/')[-1]}"
            try:
                transaction = parse_receipt_image(image_data, media_type)
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")
                return

        st.success(f"Datos extraidos (confianza: {transaction.confianza:.0%})")

        st.subheader("Datos extraidos")
        col1, col2 = st.columns(2)
        with col1:
            monto = st.number_input(
                "Monto ($)", value=transaction.monto, step=100.0,
                format="%.0f", key="foto_monto",
            )
            fecha = st.date_input(
                "Fecha", value=transaction.fecha, key="foto_fecha",
            )
        with col2:
            comercio = st.text_input(
                "Comercio", value=transaction.comercio or "", key="foto_comercio",
            )
            categoria_sugerida = transaction.categoria or ""
            categorias = get_categorias()
            categoria_opciones = ["(Sin categoria)"] + [c["nombre"] for c in categorias]
            default_idx = 0
            for i, opt in enumerate(categoria_opciones):
                if opt.lower() == categoria_sugerida.lower():
                    default_idx = i
                    break
            categoria_seleccion = st.selectbox(
                "Categoria", options=categoria_opciones,
                index=default_idx, key="foto_categoria",
            )

        concepto = st.text_input(
            "Concepto", value=transaction.concepto or "", key="foto_concepto",
        )
        descripcion = st.text_input(
            "Descripcion", value=transaction.descripcion or "", key="foto_desc",
        )

        if st.button("Guardar transaccion", key="foto_guardar"):
            if monto <= 0:
                st.error("El monto debe ser mayor a cero.")
                return

            categoria_id = None
            if categoria_seleccion != "(Sin categoria)":
                categoria_id = next(
                    c["id"] for c in categorias
                    if c["nombre"] == categoria_seleccion
                )

            insert_transaction(
                tipo="compra",
                monto=monto,
                fecha=fecha,
                descripcion=descripcion.strip() or None,
                comercio=comercio.strip() or None,
                direccion="salida",
                concepto=concepto.strip() or None,
                categoria_id=categoria_id,
            )
            st.success(f"Transaccion guardada: ${monto:,.0f} en {comercio or 'N/A'}")


def _render_manual_form() -> None:
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
