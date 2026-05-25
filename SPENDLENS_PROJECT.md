# SpendLens — Proyecto de portafolio
**Analista de datos · Python · Claude API · Streamlit**

---

## Visión general

SpendLens es una aplicación web personal de seguimiento de gastos que ingiere datos desde tres fuentes (fotos de facturas, correos bancarios y entrada manual), los procesa con IA para extraer y categorizar la información, detecta duplicados y gastos compartidos, y los presenta en un dashboard analítico interactivo.

**Objetivo de portafolio:** demostrar capacidad de diseño de soluciones de datos de extremo a extremo — desde la ingesta de datos no estructurados hasta la visualización analítica — combinando Python, SQL, y modelos de IA.

---

## Stack tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Frontend / UI | Streamlit | Rápido, pythónico, ideal para dashboards de datos |
| Backend / lógica | Python 3.11+ | Stack principal del analista |
| Base de datos | SQLite (dev) / PostgreSQL (prod) | SQLite para desarrollo local, Postgres en deploy |
| IA / extracción | Claude API (claude-sonnet-4-5) | Extracción de recibos, clasificación, detección de splits |
| Email | Gmail API (OAuth 2.0) | Lectura de correos bancarios |
| Fuzzy matching | rapidfuzz | Comparación aproximada de nombres de comercios |
| Visualización | Plotly | Gráficos interactivos dentro de Streamlit |
| Deploy | Streamlit Cloud | Gratuito, fácil, URL pública compartible |
| Control de versiones | Git + GitHub | Repositorio público para portafolio |

---

## Estructura de carpetas

```
spendlens/
│
├── README.md                  # Descripción del proyecto, instalación, uso
├── ARCHITECTURE.md            # Decisiones de diseño y diagrama de arquitectura
├── CHANGELOG.md               # Historial de cambios por versión
├── requirements.txt           # Dependencias Python
├── .env.example               # Variables de entorno necesarias (sin valores reales)
├── .gitignore
│
├── app.py                     # Punto de entrada — Streamlit app
│
├── config/
│   └── settings.py            # Configuración centralizada (rutas, umbrales, constantes)
│
├── database/
│   ├── schema.sql             # Definición de tablas
│   ├── db.py                  # Conexión y queries base
│   └── migrations/            # Scripts de migración numerados
│       └── 001_initial.sql
│
├── ingestion/                 # Capa de ingesta de datos
│   ├── __init__.py
│   ├── photo_parser.py        # Extracción desde foto de factura (Claude Vision)
│   ├── email_parser.py        # Extracción desde correos bancarios (Gmail API)
│   └── manual_entry.py        # Validación de entrada manual
│
├── processing/                # Capa de procesamiento y lógica de negocio
│   ├── __init__.py
│   ├── normalizer.py          # Normalización de montos, fechas, nombres
│   ├── categorizer.py         # Clasificación de gastos por categoría
│   ├── deduplicator.py        # Detección y fusión de duplicados
│   └── split_detector.py      # Detección de gastos compartidos / reembolsos
│
├── models/                    # Modelos de datos (dataclasses / Pydantic)
│   ├── __init__.py
│   ├── transaction.py         # Transaction, TransactionType, Source
│   └── review_item.py         # ReviewItem para cola de revisión humana
│
├── views/                     # Páginas y componentes de Streamlit
│   ├── __init__.py
│   ├── dashboard.py           # Vista principal con métricas y gráficos
│   ├── upload.py              # Vista de subida de foto / entrada manual
│   ├── review_queue.py        # Cola de revisión de duplicados y splits
│   └── transactions.py        # Lista completa de transacciones
│
├── services/                  # Integraciones externas
│   ├── __init__.py
│   ├── claude_service.py      # Wrapper de Claude API
│   └── gmail_service.py       # Wrapper de Gmail API
│
└── tests/                     # Pruebas unitarias
    ├── test_normalizer.py
    ├── test_deduplicator.py
    └── test_split_detector.py
```

---

## Esquema de base de datos

```sql
-- Transacciones principales
CREATE TABLE transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL CHECK(tipo IN ('compra', 'transferencia')),
    monto           REAL NOT NULL,
    monto_neto      REAL,           -- monto después de reembolsos (NULL = sin split)
    fecha           DATE NOT NULL,
    descripcion     TEXT,
    comercio        TEXT,           -- para compras
    contraparte     TEXT,           -- para transferencias (nombre de persona)
    direccion       TEXT CHECK(direccion IN ('entrada', 'salida')),
    concepto        TEXT,           -- texto libre del banco o del usuario
    categoria_id    INTEGER REFERENCES categorias(id),
    estado          TEXT NOT NULL DEFAULT 'activo'
                    CHECK(estado IN ('activo', 'fusionado', 'compensado')),
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fuentes de cada transacción (una transacción puede tener múltiples fuentes)
CREATE TABLE transaction_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  INTEGER NOT NULL REFERENCES transactions(id),
    fuente          TEXT NOT NULL CHECK(fuente IN ('foto', 'email', 'manual')),
    raw_data        TEXT,           -- JSON con los datos originales extraídos
    confianza       REAL,           -- score de confianza de la extracción (0-1)
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vínculos entre transacciones (duplicados fusionados, splits)
CREATE TABLE transaction_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  INTEGER NOT NULL REFERENCES transactions(id),
    linked_id       INTEGER NOT NULL REFERENCES transactions(id),
    tipo_link       TEXT NOT NULL CHECK(tipo_link IN ('duplicado', 'split', 'reembolso')),
    aprobado_por    TEXT DEFAULT 'usuario',
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cola de revisión humana
CREATE TABLE review_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL CHECK(tipo IN ('duplicado', 'split')),
    transaction_a   INTEGER NOT NULL REFERENCES transactions(id),
    transaction_b   INTEGER NOT NULL REFERENCES transactions(id),
    confianza       REAL NOT NULL,
    motivo          TEXT,           -- explicación generada por IA
    estado          TEXT NOT NULL DEFAULT 'pendiente'
                    CHECK(estado IN ('pendiente', 'aprobado', 'rechazado')),
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resuelto_en     TIMESTAMP
);

-- Categorías
CREATE TABLE categorias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    color_hex       TEXT,
    icono           TEXT
);

-- Presupuestos mensuales por categoría
CREATE TABLE presupuestos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id    INTEGER NOT NULL REFERENCES categorias(id),
    anio            INTEGER NOT NULL,
    mes             INTEGER NOT NULL CHECK(mes BETWEEN 1 AND 12),
    limite          REAL NOT NULL,
    UNIQUE(categoria_id, anio, mes)
);
```

---

## Modelos de datos (Python)

```python
# models/transaction.py
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
```

---

## Fases de desarrollo

### Fase 1 — Base (días 1–3)
- [ ] Inicializar repositorio con estructura de carpetas
- [ ] Crear esquema de base de datos y script de inicialización
- [ ] Implementar modelos de datos (dataclasses)
- [ ] Formulario de entrada manual funcional
- [ ] Vista básica de lista de transacciones

**Entregable:** puedo agregar un gasto a mano y verlo en una lista.

---

### Fase 2 — Ingesta con IA (días 4–6)
- [ ] Integrar Claude API (claude_service.py)
- [ ] Parser de foto de recibo (photo_parser.py)
- [ ] Parser de correos bancarios — Bancolombia y Nequi (email_parser.py)
- [ ] Normalización de montos y fechas (normalizer.py)
- [ ] Categorización automática (categorizer.py)

**Entregable:** subo una foto y el sistema extrae y categoriza el gasto solo.

---

### Fase 3 — Calidad de datos (días 7–9)
- [ ] Motor de deduplicación con fuzzy matching (deduplicator.py)
- [ ] Cola de revisión humana para duplicados (review_queue.py)
- [ ] Detección de gastos compartidos / reembolsos (split_detector.py)
- [ ] Vista de revisión con propuesta de vinculación

**Entregable:** el sistema detecta duplicados y splits, y me pide confirmación.

---

### Fase 4 — Dashboard (días 10–12)
- [ ] Métricas clave del mes (total, neto, por categoría)
- [ ] Gráfico de tendencia mensual (Plotly)
- [ ] Desglose por categoría con barras
- [ ] Alertas de presupuesto
- [ ] Filtros por fecha y categoría

**Entregable:** dashboard completo con todos los gastos del mes.

---

### Fase 5 — Deploy y documentación (días 13–14)
- [ ] README completo con screenshots y demo GIF
- [ ] ARCHITECTURE.md con decisiones de diseño
- [ ] Deploy en Streamlit Cloud
- [ ] Variables de entorno documentadas en .env.example

**Entregable:** URL pública compartible y repositorio de portafolio pulido.

---

## Reglas de decisión del motor de deduplicación

| Confianza | Acción automática |
|---|---|
| ≥ 90% | Fusión automática sin revisión |
| 60% – 89% | Entra a cola de revisión humana |
| < 60% | Se guardan como registros independientes |

Criterios de matching (los tres deben cumplirse):
- **Monto:** exactamente igual
- **Fecha:** diferencia ≤ 1 día
- **Comercio/contraparte:** similitud fuzzy ≥ 75% (rapidfuzz)

---

## Reglas de detección de splits

- La transferencia entrante tiene keywords de reembolso en el concepto
- El ratio reembolso/gasto original está entre 20% y 80%
- El gasto original ocurrió en los últimos 7 días
- Categoría compatible (Alimentación, Entretenimiento, etc.)

---

## Estándares de código

- **Docstrings** en todas las funciones públicas (formato Google style)
- **Type hints** en todos los parámetros y retornos
- **Nombres en español** para variables de dominio (monto, fecha, comercio)
- **Nombres en inglés** para estructuras técnicas (parser, handler, service)
- Un archivo por responsabilidad — sin módulos "utils" genéricos
- Toda llamada a Claude API pasa por `claude_service.py` — nunca directo

---

## Variables de entorno requeridas

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
DATABASE_URL=sqlite:///spendlens.db
APP_ENV=development   # development | production
```

---

## Instrucciones para Claude Code

Al iniciar sesión con Claude Code, ejecutar:

```bash
claude "Lee el archivo SPENDLENS_PROJECT.md y úsalo como referencia \
completa del proyecto. Comenzamos por la Fase 1. \
Crea la estructura de carpetas, el esquema de base de datos, \
y el módulo models/transaction.py siguiendo exactamente \
las especificaciones del documento."
```

Comando para continuar en sesiones posteriores:

```bash
claude "Continuamos con SpendLens. Lee SPENDLENS_PROJECT.md \
para contexto. Estamos en Fase [X]. \
El último entregable completado fue: [descripción]."
```

---

*Documento generado como base del proyecto SpendLens.*
*Versión 1.0 — Mayo 2026*
