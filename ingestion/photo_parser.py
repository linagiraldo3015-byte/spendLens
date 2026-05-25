from datetime import date, datetime
from pathlib import Path
from typing import Optional

from models.transaction import Direction, Source, Transaction, TransactionType
from services.claude_service import ask_json_with_image, detect_media_type

SYSTEM_PROMPT = """Eres un asistente experto en extraccion de datos de facturas y recibos colombianos.
Extrae la informacion de la imagen y responde UNICAMENTE con un JSON valido (sin texto adicional).
Si no puedes determinar un campo, usa null.
Para el monto, usa el valor total de la factura como numero sin separadores de miles.
Para la fecha, usa formato YYYY-MM-DD.
La confianza es un valor entre 0 y 1 que indica que tan seguro estas de la extraccion."""

EXTRACTION_PROMPT = """Analiza esta imagen de factura/recibo y extrae los datos en el siguiente formato JSON:

{
    "monto": <numero>,
    "fecha": "<YYYY-MM-DD>",
    "comercio": "<nombre del establecimiento>",
    "descripcion": "<descripcion breve de la compra>",
    "concepto": "<detalle principal o items>",
    "categoria_sugerida": "<una de: Alimentacion, Transporte, Entretenimiento, Salud, Hogar, Educacion, Ropa, Tecnologia, Servicios, Otros>",
    "confianza": <0.0 a 1.0>
}"""


def parse_receipt_image(image_data: bytes, media_type: str) -> Transaction:
    """Extrae datos de transaccion desde una imagen de factura usando Claude Vision."""
    data = ask_json_with_image(
        image_data=image_data,
        media_type=media_type,
        prompt=EXTRACTION_PROMPT,
        system=SYSTEM_PROMPT,
    )
    return _build_transaction(data)


def parse_receipt_file(file_path: Path) -> Transaction:
    """Extrae datos de transaccion desde un archivo de imagen de factura."""
    image_data = file_path.read_bytes()
    media_type = detect_media_type(file_path)
    return parse_receipt_image(image_data, media_type)


def _build_transaction(data: dict) -> Transaction:
    fecha = _parse_fecha(data.get("fecha"))
    return Transaction(
        tipo=TransactionType.COMPRA,
        monto=float(data.get("monto", 0)),
        fecha=fecha,
        descripcion=data.get("descripcion"),
        comercio=data.get("comercio"),
        direccion=Direction.SALIDA,
        concepto=data.get("concepto"),
        categoria=data.get("categoria_sugerida"),
        fuentes=[Source.FOTO],
        confianza=float(data.get("confianza", 0.5)),
    )


def _parse_fecha(fecha_str: Optional[str]) -> date:
    if not fecha_str:
        return date.today()
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return date.today()
