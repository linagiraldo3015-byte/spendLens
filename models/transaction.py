from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class TransactionType(str, Enum):
    COMPRA = "compra"
    TRANSFERENCIA = "transferencia"


class Source(str, Enum):
    FOTO = "foto"
    EMAIL = "email"
    MANUAL = "manual"


class Direction(str, Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"


@dataclass
class Transaction:
    tipo: TransactionType
    monto: float
    fecha: date
    descripcion: Optional[str] = None
    comercio: Optional[str] = None
    contraparte: Optional[str] = None
    direccion: Optional[Direction] = None
    concepto: Optional[str] = None
    categoria: Optional[str] = None
    monto_neto: Optional[float] = None
    fuentes: list[Source] = field(default_factory=list)
    confianza: float = 1.0
