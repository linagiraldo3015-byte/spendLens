-- SpendLens — Esquema de base de datos
-- SQLite (desarrollo) / PostgreSQL (producción)

-- Categorias (debe crearse antes de transactions por la FK)
CREATE TABLE IF NOT EXISTS categorias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    color_hex       TEXT,
    icono           TEXT
);

-- Transacciones principales
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL CHECK(tipo IN ('compra', 'transferencia')),
    monto           REAL NOT NULL,
    monto_neto      REAL,
    fecha           DATE NOT NULL,
    descripcion     TEXT,
    comercio        TEXT,
    contraparte     TEXT,
    direccion       TEXT CHECK(direccion IN ('entrada', 'salida')),
    concepto        TEXT,
    categoria_id    INTEGER REFERENCES categorias(id),
    estado          TEXT NOT NULL DEFAULT 'activo'
                    CHECK(estado IN ('activo', 'fusionado', 'compensado')),
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fuentes de cada transaccion (una transaccion puede tener multiples fuentes)
CREATE TABLE IF NOT EXISTS transaction_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  INTEGER NOT NULL REFERENCES transactions(id),
    fuente          TEXT NOT NULL CHECK(fuente IN ('foto', 'email', 'manual')),
    raw_data        TEXT,
    confianza       REAL,
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vinculos entre transacciones (duplicados fusionados, splits)
CREATE TABLE IF NOT EXISTS transaction_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  INTEGER NOT NULL REFERENCES transactions(id),
    linked_id       INTEGER NOT NULL REFERENCES transactions(id),
    tipo_link       TEXT NOT NULL CHECK(tipo_link IN ('duplicado', 'split', 'reembolso')),
    aprobado_por    TEXT DEFAULT 'usuario',
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cola de revision humana
CREATE TABLE IF NOT EXISTS review_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL CHECK(tipo IN ('duplicado', 'split')),
    transaction_a   INTEGER NOT NULL REFERENCES transactions(id),
    transaction_b   INTEGER NOT NULL REFERENCES transactions(id),
    confianza       REAL NOT NULL,
    motivo          TEXT,
    estado          TEXT NOT NULL DEFAULT 'pendiente'
                    CHECK(estado IN ('pendiente', 'aprobado', 'rechazado')),
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resuelto_en     TIMESTAMP
);

-- Presupuestos mensuales por categoria
CREATE TABLE IF NOT EXISTS presupuestos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id    INTEGER NOT NULL REFERENCES categorias(id),
    anio            INTEGER NOT NULL,
    mes             INTEGER NOT NULL CHECK(mes BETWEEN 1 AND 12),
    limite          REAL NOT NULL,
    UNIQUE(categoria_id, anio, mes)
);
