import streamlit as st

from ingestion.email_parser import importar_emails


def render() -> None:
    st.header("Importar desde Gmail")

    st.markdown(
        "Trae automáticamente tus movimientos bancarios desde los correos "
        "etiquetados como **SpendLens** en Gmail. "
        "Los correos ya importados antes se omiten para no duplicar."
    )

    st.divider()

    if st.button("Importar correos de Gmail", type="primary"):
        with st.spinner("Conectando con Gmail y procesando correos..."):
            try:
                resumen = importar_emails()
            except Exception as e:
                st.error(f"Error al importar correos: {e}")
                return

        st.success("Importación completada.")

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

        if resumen["no_reconocidas"] > 0:
            st.caption(
                f"{resumen['no_reconocidas']} correo(s) no se reconocieron como "
                "transacciones (pueden ser avisos o promociones)."
            )
    else:
        st.info("Presiona el botón para buscar y importar tus correos bancarios.")