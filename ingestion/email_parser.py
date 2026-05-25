import re
from datetime import date, datetime
from typing import Optional

from models.transaction import Direction, Source, Transaction, TransactionType

# Patrones comunes en notificaciones de Bancolombia
_BANCOLOMBIA_COMPRA = re.compile(
    r"compra por \$([0-9.,]+) en (.+?)\.\s"
    r".*?(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE | re.DOTALL,
)
_BANCOLOMBIA_TRANSFERENCIA_SALIDA = re.compile(
    r"transferencia por \$([0-9.,]+) a (.+?)\.\s"
    r".*?(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE | re.DOTALL,
)
_BANCOLOMBIA_TRANSFERENCIA_ENTRADA = re.compile(
    r"recibiste una transferencia por \$([0-9.,]+) de (.+?)\.\s"
    r".*?(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE | re.DOTALL,
)

# Patrones comunes en notificaciones de Nequi
_NEQUI_ENVIO = re.compile(
    r"enviaste \$([0-9.,]+) a (.+?)\.\s",
    re.IGNORECASE,
)
_NEQUI_RECIBO = re.compile(
    r"recibiste \$([0-9.,]+) de (.+?)\.\s",
    re.IGNORECASE,
)
_NEQUI_COMPRA = re.compile(
    r"pagaste \$([0-9.,]+) en (.+?)\.\s",
    re.IGNORECASE,
)
_NEQUI_FECHA = re.compile(r"(\d{1,2}\s+\w+\s+\d{4}|\d{2}/\d{2}/\d{4})")

_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def parse_email(subject: str, body: str) -> Optional[Transaction]:
    """Parsea un correo bancario y retorna una Transaction o None si no se reconoce."""
    text = f"{subject}\n{body}"

    if _is_bancolombia(text):
        return _parse_bancolombia(text)
    if _is_nequi(text):
        return _parse_nequi(text)
    return None


def _is_bancolombia(text: str) -> bool:
    return "bancolombia" in text.lower()


def _is_nequi(text: str) -> bool:
    return "nequi" in text.lower()


def _parse_bancolombia(text: str) -> Optional[Transaction]:
    match = _BANCOLOMBIA_COMPRA.search(text)
    if match:
        return Transaction(
            tipo=TransactionType.COMPRA,
            monto=_parse_monto(match.group(1)),
            fecha=_parse_fecha_ddmmyyyy(match.group(3)),
            comercio=match.group(2).strip(),
            direccion=Direction.SALIDA,
            concepto="Compra con tarjeta Bancolombia",
            fuentes=[Source.EMAIL],
            confianza=0.85,
        )

    match = _BANCOLOMBIA_TRANSFERENCIA_SALIDA.search(text)
    if match:
        return Transaction(
            tipo=TransactionType.TRANSFERENCIA,
            monto=_parse_monto(match.group(1)),
            fecha=_parse_fecha_ddmmyyyy(match.group(3)),
            contraparte=match.group(2).strip(),
            direccion=Direction.SALIDA,
            concepto="Transferencia Bancolombia",
            fuentes=[Source.EMAIL],
            confianza=0.85,
        )

    match = _BANCOLOMBIA_TRANSFERENCIA_ENTRADA.search(text)
    if match:
        return Transaction(
            tipo=TransactionType.TRANSFERENCIA,
            monto=_parse_monto(match.group(1)),
            fecha=_parse_fecha_ddmmyyyy(match.group(3)),
            contraparte=match.group(2).strip(),
            direccion=Direction.ENTRADA,
            concepto="Transferencia recibida Bancolombia",
            fuentes=[Source.EMAIL],
            confianza=0.85,
        )

    return None


def _parse_nequi(text: str) -> Optional[Transaction]:
    fecha = _extract_nequi_fecha(text)

    match = _NEQUI_COMPRA.search(text)
    if match:
        return Transaction(
            tipo=TransactionType.COMPRA,
            monto=_parse_monto(match.group(1)),
            fecha=fecha,
            comercio=match.group(2).strip(),
            direccion=Direction.SALIDA,
            concepto="Pago con Nequi",
            fuentes=[Source.EMAIL],
            confianza=0.80,
        )

    match = _NEQUI_ENVIO.search(text)
    if match:
        return Transaction(
            tipo=TransactionType.TRANSFERENCIA,
            monto=_parse_monto(match.group(1)),
            fecha=fecha,
            contraparte=match.group(2).strip(),
            direccion=Direction.SALIDA,
            concepto="Envio Nequi",
            fuentes=[Source.EMAIL],
            confianza=0.80,
        )

    match = _NEQUI_RECIBO.search(text)
    if match:
        return Transaction(
            tipo=TransactionType.TRANSFERENCIA,
            monto=_parse_monto(match.group(1)),
            fecha=fecha,
            contraparte=match.group(2).strip(),
            direccion=Direction.ENTRADA,
            concepto="Recibido por Nequi",
            fuentes=[Source.EMAIL],
            confianza=0.80,
        )

    return None


def _parse_monto(raw: str) -> float:
    cleaned = raw.replace(".", "").replace(",", ".")
    return float(cleaned)


def _parse_fecha_ddmmyyyy(raw: str) -> date:
    try:
        return datetime.strptime(raw.strip(), "%d/%m/%Y").date()
    except ValueError:
        return date.today()


def _extract_nequi_fecha(text: str) -> date:
    match = _NEQUI_FECHA.search(text)
    if not match:
        return date.today()
    raw = match.group(1)
    if "/" in raw:
        return _parse_fecha_ddmmyyyy(raw)
    return _parse_fecha_texto(raw)


def _parse_fecha_texto(raw: str) -> date:
    """Parsea fechas como '25 mayo 2026'."""
    parts = raw.lower().split()
    if len(parts) != 3:
        return date.today()
    try:
        dia = int(parts[0])
        mes = _MESES.get(parts[1])
        anio = int(parts[2])
        if mes:
            return date(anio, mes, dia)
    except (ValueError, TypeError):
        pass
    return date.today()
