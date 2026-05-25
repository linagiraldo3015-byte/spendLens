from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .transaction import Transaction


class ReviewType(str, Enum):
    DUPLICADO = "duplicado"
    SPLIT = "split"


class ReviewStatus(str, Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


@dataclass
class ReviewItem:
    tipo: ReviewType
    transaction_a: Transaction
    transaction_b: Transaction
    confianza: float
    motivo: Optional[str] = None
    estado: ReviewStatus = ReviewStatus.PENDIENTE
    creado_en: Optional[datetime] = None
    resuelto_en: Optional[datetime] = None
