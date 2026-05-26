import sqlite3
import json
from datetime import date
from typing import Optional

from config.settings import DB_PATH, SCHEMA_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    schema = SCHEMA_PATH.read_text()
    conn = get_connection()
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def insert_transaction(
    tipo: str,
    monto: float,
    fecha: date,
    descripcion: Optional[str] = None,
    comercio: Optional[str] = None,
    contraparte: Optional[str] = None,
    direccion: Optional[str] = None,
    concepto: Optional[str] = None,
    categoria_id: Optional[int] = None,
) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO transactions
                (tipo, monto, fecha, descripcion, comercio, contraparte,
                 direccion, concepto, categoria_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tipo, monto, fecha.isoformat(), descripcion, comercio,
             contraparte, direccion, concepto, categoria_id),
        )
        transaction_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO transaction_sources (transaction_id, fuente, confianza)
            VALUES (?, 'manual', 1.0)
            """,
            (transaction_id,),
        )
        conn.commit()
        return transaction_id
    finally:
        conn.close()

def email_ya_importado(message_id: str) -> bool:
    """Devuelve True si ya existe una transacción importada de ese correo."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT 1 FROM transaction_sources
            WHERE fuente = 'email'
              AND raw_data LIKE ?
            LIMIT 1
            """,
            (f'%"message_id": "{message_id}"%',),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def insert_email_transaction(
    tipo: str,
    monto: float,
    fecha: date,
    message_id: str,
    descripcion: Optional[str] = None,
    comercio: Optional[str] = None,
    contraparte: Optional[str] = None,
    direccion: Optional[str] = None,
    concepto: Optional[str] = None,
    categoria_id: Optional[int] = None,
    confianza: float = 0.90,
) -> Optional[int]:
    """Inserta una transacción desde un correo.

    Si el correo ya fue importado (mismo message_id), no hace nada
    y devuelve None.
    """
    if email_ya_importado(message_id):
        return None
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO transactions
                (tipo, monto, fecha, descripcion, comercio, contraparte,
                 direccion, concepto, categoria_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tipo, monto, fecha.isoformat(), descripcion, comercio,
             contraparte, direccion, concepto, categoria_id),
        )
        transaction_id = cursor.lastrowid
        raw_data = json.dumps({"message_id": message_id})
        conn.execute(
            """
            INSERT INTO transaction_sources
                (transaction_id, fuente, raw_data, confianza)
            VALUES (?, 'email', ?, ?)
            """,
            (transaction_id, raw_data, confianza),
        )
        conn.commit()
        return transaction_id
    finally:
        conn.close()
        
def get_all_transactions() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.*, c.nombre AS categoria_nombre
            FROM transactions t
            LEFT JOIN categorias c ON t.categoria_id = c.id
            WHERE t.estado = 'activo'
            ORDER BY t.fecha DESC, t.creado_en DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_categorias() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, nombre FROM categorias ORDER BY nombre"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def insert_categoria(nombre: str) -> int:
    nombre = nombre.strip().title()
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM categorias WHERE LOWER(nombre) = LOWER(?)", (nombre,)
        ).fetchone()
        if existing:
            raise sqlite3.IntegrityError(f"Categoria '{nombre}' ya existe")
        cursor = conn.execute(
            "INSERT INTO categorias (nombre) VALUES (?)", (nombre,)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Base de datos inicializada en {DB_PATH}")
