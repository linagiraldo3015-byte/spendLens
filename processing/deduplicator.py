"""Detección de transacciones duplicadas entre distintas fuentes."""

from datetime import date, datetime

from rapidfuzz import fuzz

from config.settings import (
    DEDUP_COMERCIO_AUTO_THRESHOLD,
    DEDUP_DATE_TOLERANCE_DAYS,
    DEDUP_FUZZY_THRESHOLD,
)


def _nombre_comparable(t: dict) -> str:
    """Devuelve el texto a comparar: comercio para compras, contraparte para transferencias."""
    nombre = t.get("comercio") or t.get("contraparte") or ""
    return nombre.strip().lower()


def _es_par_correo_correo(t1: dict, t2: dict) -> bool:
    """True si ambas transacciones provienen de correo (no se deben fusionar)."""
    return "email" in t1.get("fuentes", []) and "email" in t2.get("fuentes", [])

def _es_par_manual_manual(t1: dict, t2: dict) -> bool:
    """True si ambas transacciones fueron ingresadas manualmente."""
    return "manual" in t1.get("fuentes", []) and "manual" in t2.get("fuentes", [])

def _to_date(valor) -> date:
    """Normaliza una fecha que puede venir como str o date."""
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()


def _dias_entre(t1: dict, t2: dict) -> int:
    """Diferencia absoluta en días entre las fechas de dos transacciones."""
    d1 = _to_date(t1["fecha"])
    d2 = _to_date(t2["fecha"])
    return abs((d1 - d2).days)


def detectar_duplicados(transacciones: list[dict]) -> list[dict]:
    """Compara transacciones de a pares y detecta posibles duplicados.

    Devuelve una lista de pares sospechosos. Cada par es un dict con:
      - 'a', 'b': las dos transacciones
      - 'similitud': puntaje de similitud de comercio (0-100)
      - 'clasificacion': 'auto' (fusión automática) o 'revision' (cola)
    """
    resultados = []
    n = len(transacciones)

    for i in range(n):
        for j in range(i + 1, n):
            a = transacciones[i]
            b = transacciones[j]

            # 1. Solo comparar transacciones del mismo tipo
            if a.get("tipo") != b.get("tipo"):
                continue

            # 2. Nunca fusionar dos transacciones que vienen de correo
            if _es_par_correo_correo(a, b):
                continue

            # 3. Los montos deben ser exactamente iguales
            if a.get("monto") != b.get("monto"):
                continue

            # 4. Las fechas deben estar dentro de la tolerancia
            if _dias_entre(a, b) > DEDUP_DATE_TOLERANCE_DAYS:
                continue

            # 5. Similitud de comercio/contraparte
            similitud = fuzz.ratio(_nombre_comparable(a), _nombre_comparable(b))

            if similitud >= DEDUP_COMERCIO_AUTO_THRESHOLD:
                clasificacion = "auto"
            elif similitud >= DEDUP_FUZZY_THRESHOLD:
                clasificacion = "revision"
            else:
                continue

            # Los pares manual-manual nunca se fusionan automáticamente:
            # una entrada manual repetida puede ser una compra real distinta.
            if clasificacion == "auto" and _es_par_manual_manual(a, b):
                clasificacion = "revision"

            resultados.append({
                "a": a,
                "b": b,
                "similitud": similitud,
                "clasificacion": clasificacion,
            })

    return resultados
def procesar_duplicados() -> dict:
    """Detecta duplicados, fusiona los automáticos y encola los dudosos.

    - Pares 'auto': se fusionan automáticamente (se conserva el de menor id).
    - Pares 'revision': se agregan a la cola de revisión humana.

    Devuelve un resumen con conteos.
    """
    from database.db import (
        agregar_a_review_queue,
        fusionar_transacciones,
        get_transactions_con_fuentes,
    )

    transacciones = get_transactions_con_fuentes()
    pares = detectar_duplicados(transacciones)

    fusionados = 0
    encolados = 0

    for par in pares:
        id_a = par["a"]["id"]
        id_b = par["b"]["id"]
        id_principal = min(id_a, id_b)
        id_secundaria = max(id_a, id_b)

        if par["clasificacion"] == "auto":
            fusionar_transacciones(id_principal, id_secundaria)
            fusionados += 1
        else:
            motivo = f"Posible duplicado — similitud {par['similitud']:.0f}%"
            resultado = agregar_a_review_queue(
                transaction_a=id_principal,
                transaction_b=id_secundaria,
                confianza=par["similitud"] / 100,
                motivo=motivo,
            )
            if resultado is not None:
                encolados += 1

    return {
        "pares_detectados": len(pares),
        "fusionados": fusionados,
        "encolados": encolados,
    }