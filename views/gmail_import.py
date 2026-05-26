from datetime import date

import streamlit as st

from ingestion.email_parser import importar_emails

_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def render() -> None:
    st.header("Importar desde Gmail")

    st.markdown(
        "Trae automáticamente tus movimientos bancarios desde los correos "
        "etiquetados como **SpendLens** en Gmail. "
        "Los correos ya importados antes se omiten para no duplicar."
    )

    st.divider()

    hoy = date.today()

    col_mes, col_anio = st.columns(2)
    with col_mes:
        mes_nombre = st.selectbox(
            "Mes",
            options=_MESES,
            index=hoy.month - 1,
        )
        mes = _MESES.index(mes_nombre) + 1
    with col_anio:
        anios = list(range(2024, hoy.year + 1))
        anio = st.selectbox(
            "Año",
            options=anios,
            index=anios.index(hoy.year),
        )

    if st.button("Importar correos de Gmail", type="primary"):
        with st.spinner(f"Importando correos de {mes_nombre} {anio}..."):
            try:
                resumen = importar_emails(anio, mes)
            except Exception as e:
                st.error(f"Error al importar correos: {e}")
                return

        st.success(f"Importación de {mes_nombre} {anio} completada.")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Correos revisados", resumen["total"])
        col2.metric("Importadas", resumen["importadas"])
        col3.metric("Ya existían", resumen["duplicadas"])
        col4.metric("No reconocidas", resumen["no_reconocidas"])

        if resumen["importadas"] > 0:
            st.info(
                f"Se agregaron {resumen['importadas']} transacciones nuevas. "
                "Revísalas en la sección Transacciones."
            )
        elif resumen["duplicadas"] > 0 and resumen["importadas"] == 0:
            st.info("No hay correos nuevos: todo ya estaba importado.")
        elif resumen["total"] == 0:
            st.info("No se encontraron correos en ese mes.")

        if resumen["no_reconocidas"] > 0:
            st.caption(
                f"{resumen['no_reconocidas']} correo(s) no se reconocieron como "
                "transacciones (pueden ser avisos o promociones)."
            )
    else:
        st.info("Elige un mes y presiona el botón para importar tus correos bancarios.")