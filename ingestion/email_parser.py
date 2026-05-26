import re
from datetime import date, datetime
from typing import Optional

from models.transaction import Direction, Source, Transaction, TransactionType

# Patrones reales de notificaciones Bancolombia
# Formato 1: "Transferiste $36,000.00 desde tu cuenta 3545 a la cuenta *3128402948 el 24/05/2026 a las 19:41"
_BANCOLOMBIA_TRANSFERISTE = re.compile(
    r"Transferiste \$([0-9.,]+) desde tu (?:cuenta|producto) \*?\S+ a la cuenta (\S+?) ,?el (\d{2}/\d{2}/\d{4}) (?:a las )?(\d{2}:\d{2})",
    re.IGNORECASE,
)
# Formato 2: "Recibiste una transferencia por $53,700 de WALTER GUETTE en tu cuenta **3545, el 23/05/2026 a las 11:18"
_BANCOLOMBIA_RECIBISTE = re.compile(
    r"Recibiste una transferencia por \$([0-9.,]+) de (.+?) en tu (?:cuenta|producto) \*{0,2}\S+,? el (\d{2}/\d{2}/\d{4}) (?:a las )?(\d{2}:\d{2})",
    re.IGNORECASE,
)
# Formato 3: "Pagaste $165,000.00 a Kushki Colombia SA desde tu producto *3545 el 21/05/2026 12:40:45"
_BANCOLOMBIA_PAGASTE = re.compile(
    r"Pagaste \$([0-9.,]+) (?:a|en) (.+?) desde tu (?:cuenta|producto) \*?\S+ el (\d{2}/\d{2}/\d{4}) (?:a las )?(\d{2}:\d{2})",
    re.IGNORECASE,
)
# Formato legacy: "Compraste $50,000.00 en EXITO POBLADO el 24/05/2026 a las 14:30"
_BANCOLOMBIA_COMPRASTE = re.compile(
    r"Compraste \$([0-9.,]+) en (.+?) el (\d{2}/\d{2}/\d{4}) (?:a las )?(\d{2}:\d{2})",
    re.IGNORECASE,
)
# Formato 5: "Transferiste $61,500.00 por Boton Bancolombia a PASMOL SAS desde producto *3545. 24/05/2026 07:43:11"
_BANCOLOMBIA_BOTON = re.compile(
    r"Transferiste \$([0-9.,]+) por Boton Bancolombia a (.+?) desde (?:tu )?(?:cuenta|producto) \*?\S+\.? (\d{2}/\d{2}/\d{4}) (\d{2}:\d{2})(?::\d{2})?",
    re.IGNORECASE,
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
    raw_text = f"{subject}\n{body}"
    text = _clean_body(raw_text)

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
    patterns = [
        ("BOTON", _BANCOLOMBIA_BOTON),
        ("TRANSFERISTE", _BANCOLOMBIA_TRANSFERISTE),
        ("COMPRASTE", _BANCOLOMBIA_COMPRASTE),
        ("RECIBISTE", _BANCOLOMBIA_RECIBISTE),
        ("PAGASTE", _BANCOLOMBIA_PAGASTE),
    ]
    for name, pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        if name == "BOTON":
            return Transaction(
                tipo=TransactionType.COMPRA,
                monto=_parse_monto(match.group(1)),
                fecha=_parse_fecha_ddmmyyyy(match.group(3)),
                comercio=match.group(2).strip(),
                direccion=Direction.SALIDA,
                concepto=f"Pago Botón Bancolombia a {match.group(2).strip()} a las {match.group(4)}",
                fuentes=[Source.EMAIL],
                confianza=0.90,
            )
        if name == "TRANSFERISTE":
            return Transaction(
                tipo=TransactionType.TRANSFERENCIA,
                monto=_parse_monto(match.group(1)),
                fecha=_parse_fecha_ddmmyyyy(match.group(3)),
                contraparte=match.group(2).strip(),
                direccion=Direction.SALIDA,
                concepto=f"Transferencia Bancolombia a {match.group(2).strip()} a las {match.group(4)}",
                fuentes=[Source.EMAIL],
                confianza=0.90,
            )
        if name == "COMPRASTE":
            return Transaction(
                tipo=TransactionType.COMPRA,
                monto=_parse_monto(match.group(1)),
                fecha=_parse_fecha_ddmmyyyy(match.group(3)),
                comercio=match.group(2).strip(),
                direccion=Direction.SALIDA,
                concepto=f"Compra Bancolombia a las {match.group(4)}",
                fuentes=[Source.EMAIL],
                confianza=0.90,
            )
        if name == "RECIBISTE":
            return Transaction(
                tipo=TransactionType.TRANSFERENCIA,
                monto=_parse_monto(match.group(1)),
                fecha=_parse_fecha_ddmmyyyy(match.group(3)),
                contraparte=match.group(2).strip(),
                direccion=Direction.ENTRADA,
                concepto=f"Transferencia recibida Bancolombia a las {match.group(4)}",
                fuentes=[Source.EMAIL],
                confianza=0.90,
            )
        if name == "PAGASTE":
            return Transaction(
                tipo=TransactionType.COMPRA,
                monto=_parse_monto(match.group(1)),
                fecha=_parse_fecha_ddmmyyyy(match.group(3)),
                comercio=match.group(2).strip(),
                direccion=Direction.SALIDA,
                concepto=f"Pago Bancolombia a las {match.group(4)}",
                fuentes=[Source.EMAIL],
                confianza=0.90,
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
    """Parsea montos en formato colombiano.

    Soporta formatos:
      - $36,000.00 (coma=miles, punto=decimal)
      - $53,700 (coma=miles, sin decimal)
      - $85.000 (punto=miles, sin decimal)
    """
    if "," in raw and "." in raw:
        cleaned = raw.replace(",", "")
    elif "," in raw:
        parts = raw.split(",")
        if len(parts[-1]) == 3:
            cleaned = raw.replace(",", "")
        else:
            cleaned = raw.replace(",", ".")
    else:
        cleaned = raw.replace(".", "").replace(",", ".")
    return float(cleaned)


_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_BRACKET_IMG_PATTERN = re.compile(r"\[https?://\S+\]", re.IGNORECASE)
_MULTI_SPACE = re.compile(r"\s+")


_GLUED_WORDS = re.compile(r"([a-záéíóúñ!])([A-ZÁÉÍÓÚÑ¡])")


def _clean_body(text: str) -> str:
    """Elimina URLs, referencias a imagenes y normaliza espacios."""
    text = text.replace("\xa0", " ").replace("​", "")
    text = _BRACKET_IMG_PATTERN.sub(" ", text)
    text = _URL_PATTERN.sub(" ", text)
    text = _GLUED_WORDS.sub(r"\1 \2", text)
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


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

def importar_emails(anio: int, mes: int) -> dict:
    """Trae correos de Gmail de un mes, los parsea y guarda los nuevos en la BD.

    Args:
        anio: año a importar (ej. 2026)
        mes: mes a importar (1-12)

    Devuelve un resumen con conteos:
      - importadas: transacciones nuevas guardadas
      - duplicadas: correos ya importados antes (saltados)
      - no_reconocidas: correos que no se pudieron parsear
    """
    from services.gmail_service import list_bank_emails
    from database.db import email_ya_importado, insert_email_transaction

    emails = list_bank_emails(anio, mes)
    importadas = 0
    duplicadas = 0
    no_reconocidas = 0

    for em in emails:
        if email_ya_importado(em.message_id):
            duplicadas += 1
            continue
        transaction = parse_email(em.subject, em.body)
        if transaction is None:
            no_reconocidas += 1
            continue
        insert_email_transaction(
            tipo=transaction.tipo.value,
            monto=transaction.monto,
            fecha=transaction.fecha,
            message_id=em.message_id,
            descripcion=transaction.descripcion,
            comercio=transaction.comercio,
            contraparte=transaction.contraparte,
            direccion=transaction.direccion.value if transaction.direccion else None,
            concepto=transaction.concepto,
            confianza=transaction.confianza,
        )
        importadas += 1

    return {
        "total": len(emails),
        "importadas": importadas,
        "duplicadas": duplicadas,
        "no_reconocidas": no_reconocidas,
    }