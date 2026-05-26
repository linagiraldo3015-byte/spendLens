import streamlit as st

from database.db import (
    fusionar_transacciones,
    get_review_queue_pendientes,
    resolver_review_item,
)


def render() -> None:
    st.header("Cola de revisión")

    items = get_review_queue_pendientes()

    if not items:
        st.success("No hay nada pendiente de revisión.")
        st.caption(
            "Cuando el detector de duplicados encuentre casos dudosos, "
            "aparecerán aquí para que decidas."
        )
        return

    st.caption(
        f"{len(items)} caso(s) pendiente(s). Revisa cada par y decide "
        "si son la misma transacción o dos movimientos distintos."
    )

    for item in items:
        _render_item(item)


def _render_item(item: dict) -> None:
    a = item["trans_a"]
    b = item["trans_b"]

    if a is None or b is None:
        return

    st.divider()
    st.markdown(f"**{item['motivo']}**")

    col_a, col_b = st.columns(2)
    with col_a:
        _render_transaccion(a, "Transacción A")
    with col_b:
        _render_transaccion(b, "Transacción B")

    col_fusionar, col_distintas = st.columns(2)
    with col_fusionar:
        if st.button(
            "Fusionar (son la misma)",
            key=f"fusionar_{item['id']}",
            type="primary",
        ):
            id_principal = min(a["id"], b["id"])
            id_secundaria = max(a["id"], b["id"])
            fusionar_transacciones(id_principal, id_secundaria)
            resolver_review_item(item["id"], "aprobado")
            st.rerun()
    with col_distintas:
        if st.button(
            "Son distintas",
            key=f"distintas_{item['id']}",
        ):
            resolver_review_item(item["id"], "rechazado")
            st.rerun()


def _render_transaccion(t: dict, titulo: str) -> None:
    nombre = t.get("comercio") or t.get("contraparte") or "—"
    st.markdown(f"**{titulo}**")
    st.text(f"Monto:    ${t['monto']:,.0f}")
    st.text(f"Fecha:    {t['fecha']}")
    st.text(f"Tipo:     {t['tipo']}")
    st.text(f"Comercio: {nombre}")
    st.text(f"Concepto: {t.get('concepto') or '—'}")