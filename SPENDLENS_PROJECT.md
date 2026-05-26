# SpendLens — Referencia del proyecto

App web personal de seguimiento de gastos que ingiere datos desde tres fuentes (fotos de facturas, correos bancarios, entrada manual), extrae y categoriza con IA, detecta duplicados/splits, y presenta un dashboard analítico.

**Stack:** Python 3.11+ · Streamlit · Claude API (claude-sonnet-4-5) · Gmail API (OAuth 2.0) · SQLite · Plotly · BeautifulSoup4  
**Repo:** https://github.com/linagiraldo3015-byte/spendLens  
**Objetivo:** proyecto de portafolio — demostrar diseño de solución de datos end-to-end.

---

## Estructura de carpetas

```
spendLens/
├── app.py                          # Punto de entrada Streamlit (sidebar + routing: Registrar, Transacciones, Importar Gmail)
├── requirements.txt                # Dependencias pinneadas
├── .env.example                    # Template de variables de entorno
├── .gitignore                      # Excluye venv/, .env, *.db, token.json, credentials.json
├── spendlens.db                    # SQLite local (gitignored)
├── credentials.json                # OAuth client secret de Google Cloud (gitignored)
├── token.json                      # Token OAuth generado al autenticar (gitignored)
│
├── config/
│   └── settings.py                 # Constantes, rutas, umbrales de dedup/split, config Gmail
│
├── database/
│   ├── schema.sql                  # DDL completo: transactions, categorias, transaction_sources,
│   │                               #   transaction_links, review_queue, presupuestos
│   ├── db.py                       # Conexión SQLite, init_db(), CRUD, email_ya_importado(), insert_email_transaction()
│   └── migrations/
│       └── 001_initial.sql         # Ejecuta schema.sql
│
├── models/
│   ├── __init__.py
│   ├── transaction.py              # Dataclass Transaction + enums TransactionType, Source, Direction
│   └── review_item.py              # Dataclass ReviewItem + enums ReviewType, ReviewStatus
│
├── ingestion/
│   ├── __init__.py
│   ├── photo_parser.py             # Extracción de recibos con Claude Vision → Transaction
│   └── email_parser.py             # Regex parser (5 Bancolombia + 3 Nequi), importar_emails() orquestador
│
├── processing/
│   └── __init__.py                 # Vacío — módulos pendientes (normalizer, deduplicator, etc.)
│
├── services/
│   ├── __init__.py
│   ├── claude_service.py           # Wrapper Claude API: ask_text, ask_with_image, ask_json, ask_json_with_image
│   └── gmail_service.py            # OAuth 2.0 auth, list_bank_emails(anio, mes), fetch_email, build_bank_query(anio, mes)
│
└── views/
    ├── __init__.py
    ├── upload.py                   # Tabs: entrada manual + foto de factura con preview/edición
    ├── transactions.py             # Lista con filtros (mes, año, categoría, tipo) + métricas dinámicas + dataframe
    └── gmail_import.py             # Vista "Importar desde Gmail": selectores mes/año, trae, parsea, deduplica y guarda
```

### Archivos planificados pero NO creados aún

```
ingestion/manual_entry.py           # Validación de entrada manual (lógica inline en views/upload.py)
processing/normalizer.py            # Normalización de montos, fechas, nombres
processing/categorizer.py           # Clasificación automática por categoría
processing/deduplicator.py          # Detección y fusión de duplicados (rapidfuzz)
processing/split_detector.py        # Detección de gastos compartidos / reembolsos
views/dashboard.py                  # Dashboard con gráficos Plotly
views/review_queue.py               # Cola de revisión humana para duplicados/splits
tests/                              # No existe — sin tests unitarios
```

---

## Estado por fases

### Fase 1 — Base ✅

- [x] Repositorio inicializado con estructura de carpetas
- [x] Esquema de base de datos (`schema.sql`) con 6 tablas
- [x] Modelos de datos: `Transaction`, `ReviewItem` con enums
- [x] `db.py`: `init_db()`, `insert_transaction()`, `get_all_transactions()`, `get_categorias()`, `insert_categoria()`
- [x] Vista `upload.py`: formulario manual con tipo, monto, fecha, dirección, categoría, comercio/contraparte
- [x] Vista `transactions.py`: lista con métricas resumen y dataframe
- [x] `app.py`: navegación sidebar con dos páginas
- [x] Creación de categorías inline en el formulario

### Fase 2 — Ingesta con IA ✅

- [x] `claude_service.py`: wrapper completo (text, image, json, json+image)
- [x] `photo_parser.py`: extracción de recibos con Claude Vision + preview editable en UI
- [x] `gmail_service.py`: autenticación OAuth 2.0, query por label `SpendLens`, fetch y decode de emails
- [x] `email_parser.py`: regex patterns para Bancolombia (5 formatos) y Nequi (3 formatos)
- [x] `_clean_body()`: limpieza de URLs, imágenes, caracteres especiales, palabras pegadas
- [x] `_parse_monto()`: manejo de formatos colombianos ($36,000.00 / $53,700 / $85.000)
- [x] ~~🐛 email_parser.py no hace match con correos reales de Bancolombia~~ → ✅ **Resuelto** (ver sección Bug resuelto)
- [x] `_extract_body()`: fallback a HTML con BeautifulSoup cuando no hay text/plain
- [x] `build_bank_query()`: removido filtro `is:unread` para no perder correos ya abiertos
- [x] Validado contra 12 correos reales: 11 parsean correctamente, 1 retorna `None` correctamente (aviso de rechazo, no transacción)
- [x] `importar_emails(anio, mes)`: orquestador que trae correos de Gmail → parsea → deduplica por `message_id` → guarda en BD
- [x] `db.py`: `email_ya_importado(message_id)` e `insert_email_transaction()` con `message_id` en `raw_data` JSON
- [x] Vista `gmail_import.py`: pantalla "Importar desde Gmail" con selectores de mes y año, integrada en `app.py`
- [x] Deduplicación por `message_id` implementada y probada (re-importar da 0 nuevas, todas duplicadas)
- [x] `build_bank_query(anio, mes)`: query por rango de mes con `after:/before:` en vez de `newer_than:` (importación de cualquier mes histórico)
- [x] Vista `transactions.py`: filtros de mes, año, categoría y tipo con métricas que se recalculan según el filtro

### Fase 3 — Procesamiento y calidad de datos ⏳

- [ ] `normalizer.py`: normalización centralizada de comercios (EXITO POBLADO → Éxito)
- [ ] `categorizer.py`: clasificación automática con Claude
- [ ] `deduplicator.py`: motor de deduplicación con rapidfuzz
- [ ] Cola de revisión humana (`review_queue.py` vista)
- [ ] `split_detector.py`: detección de gastos compartidos
- [ ] Vista de revisión con propuesta de vinculación

### Fase 4 — Dashboard ⏳

- [ ] Métricas clave del mes (total, neto, por categoría)
- [ ] Gráfico de tendencia mensual (Plotly)
- [ ] Desglose por categoría
- [ ] Alertas de presupuesto
- [ ] Filtros por fecha y categoría

### Fase 5 — Deploy y documentación ⏳

- [ ] README con screenshots y demo GIF
- [ ] ARCHITECTURE.md
- [ ] Deploy en Streamlit Cloud
- [ ] Documentación de .env.example completa

---

## ✅ Bug resuelto — email_parser.py no parseaba correos de Bancolombia

**Síntoma original:** `parse_email()` retornaba `None` para correos reales de Bancolombia que llegaban via Gmail API.

**Causa raíz (triple):**

1. **`_MULTI_SPACE` usaba `r"[ \t]+"`** — no colapsaba los saltos de línea `\r\n` que Gmail insertaba en medio de las frases, rompiendo los regex. **Fix:** cambiado a `r"\s+"`.
2. **Faltaba formato de Botón Bancolombia** — pagos a comercios tipo "Transferiste $61,500.00 por Boton Bancolombia a PASMOL SAS desde producto *3545". **Fix:** se agregó regex `_BANCOLOMBIA_BOTON`, clasificado como COMPRA (el destinatario es un comercio, no una persona).
3. **Correos solo con HTML** — algunos correos de Bancolombia llegan solo con `text/html`, sin `text/plain`, así que `_extract_body()` devolvía cuerpo vacío. **Fix:** se agregó fallback a HTML usando BeautifulSoup (`_find_part_by_mime` y `_html_to_text`).

**Otros cambios relacionados:**
- Se quitó `is:unread` del query de Gmail en `build_bank_query()` para no perder transacciones de correos ya abiertos.
- Nueva dependencia: `beautifulsoup4==4.14.3` (en `requirements.txt`).

**Validación:** parser probado contra 12 correos reales de Bancolombia — 11 parsean correctamente, 1 retorna `None` correctamente (es un aviso de rechazo de factura, no una transacción).

---

## Formatos reales de correos Bancolombia

Los correos de notificación de Bancolombia (`alertasynotificaciones@bancolombia.com.co`) usan estos formatos en el body:

### Transferencia enviada
```
Transferiste $36,000.00 desde tu cuenta 3545 a la cuenta *3128402948 el 24/05/2026 a las 19:41
```

### Transferencia recibida
```
Recibiste una transferencia por $53,700 de WALTER GUETTE en tu cuenta **3545, el 23/05/2026 a las 11:18
```

### Pago a comercio
```
Pagaste $165,000.00 a Kushki Colombia SA desde tu producto *3545 el 21/05/2026 12:40:45
```

### Compra
```
Compraste $50,000.00 en EXITO POBLADO el 24/05/2026 a las 14:30
```

### Pago por Botón Bancolombia
```
Transferiste $61,500.00 por Boton Bancolombia a PASMOL SAS desde producto *3545. 24/05/2026 07:43:11
```
> Clasificado como COMPRA (el destinatario es un comercio, no una persona).

**Notas sobre los formatos:**
- Los montos usan coma como separador de miles y punto para decimales (`$36,000.00`), o solo coma de miles sin decimales (`$53,700`)
- Las cuentas aparecen con `*`, `**`, o sin asterisco
- La hora puede venir como `a las HH:MM` o directamente `HH:MM:SS`
- Puede haber coma antes de `el` en "Recibiste" (`**3545, el`)
- Palabras como `cuenta` y `producto` se usan intercambiablemente

---

## Decisiones de diseño

### Categorías
Predefinidas en la tabla `categorias`, creadas por el usuario desde la UI. Sugerencias del photo_parser via Claude:
`Alimentacion`, `Transporte`, `Entretenimiento`, `Salud`, `Hogar`, `Educacion`, `Ropa`, `Tecnologia`, `Servicios`, `Otros`

### Etiqueta Gmail
Se usa la etiqueta `SpendLens` en Gmail para filtrar correos bancarios. El query es:
```
after:YYYY/MM/01 before:YYYY/MM+1/01 label:SpendLens
```
> `build_bank_query(anio, mes)` construye el rango con `after:/before:` (antes usaba `newer_than:`). Permite importar cualquier mes histórico. La deduplicación por `message_id` ya está implementada en `db.py`.

El usuario debe crear la etiqueta manualmente en Gmail y aplicar un filtro para que los correos de `alertasynotificaciones@bancolombia.com.co` y `notificaciones@nequi.com.co` reciban esa etiqueta.

### transaction_sources
Una transacción puede tener múltiples fuentes (`foto`, `email`, `manual`). La tabla `transaction_sources` registra cada fuente con su `raw_data` (JSON original) y `confianza` (0–1). Se insertan fuentes `manual` (confianza `1.0`) y `email` (confianza `0.9`, con `message_id` en `raw_data` JSON) desde `db.py`.

### Formato de montos colombianos
`_parse_monto()` en `email_parser.py` maneja tres formatos:
- `$36,000.00` → coma=miles, punto=decimal → `36000.00`
- `$53,700` → coma=miles, sin decimal → `53700`
- `$85.000` → punto=miles, sin decimal → `85000`

### Umbrales de deduplicación (configurados, no implementados)
```python
DEDUP_CONFIDENCE_AUTO = 0.90     # ≥90% → fusión automática
DEDUP_CONFIDENCE_REVIEW = 0.60   # 60-89% → cola de revisión
DEDUP_DATE_TOLERANCE_DAYS = 1    # ±1 día
DEDUP_FUZZY_THRESHOLD = 75       # rapidfuzz score mínimo
```

### Detección de splits (configurada, no implementada)
```python
SPLIT_RATIO_MIN = 0.20           # ratio reembolso/gasto ≥20%
SPLIT_RATIO_MAX = 0.80           # ratio reembolso/gasto ≤80%
SPLIT_LOOKBACK_DAYS = 7          # buscar gasto original en últimos 7 días
```

### Idioma del código
- Variables de dominio en español: `monto`, `fecha`, `comercio`, `contraparte`, `concepto`
- Estructuras técnicas en inglés: `parser`, `service`, `handler`
- UI en español

---

## Configuración Gmail

| Item | Valor |
|---|---|
| Cuenta | jorgepaternina189@gmail.com |
| Etiqueta | `SpendLens` |
| Remitentes bancarios | `alertasynotificaciones@bancolombia.com.co`, `notificaciones@nequi.com.co`, `notificaciones@nequi.com` |
| Scopes | `gmail.readonly` |
| Archivos locales | `credentials.json` (OAuth client secret), `token.json` (token generado) |
| Ambos en .gitignore | ✅ |

---

## Variables de entorno

```bash
ANTHROPIC_API_KEY=sk-ant-...          # API key de Anthropic
GMAIL_CLIENT_ID=...                    # OAuth client ID de Google Cloud
GMAIL_CLIENT_SECRET=...                # OAuth client secret
DATABASE_URL=sqlite:///spendlens.db    # URL de la base de datos
APP_ENV=development                    # development | production
```

---

## Próximos pasos (por prioridad)

1. **categorizer.py** — clasificación automática usando Claude para transacciones sin categoría
2. **normalizer.py** — normalización centralizada de comercios (EXITO POBLADO → Éxito)
3. **deduplicator.py** — motor de deduplicación con rapidfuzz usando los umbrales de `settings.py`
4. **review_queue.py** (vista) — cola de revisión humana para duplicados y splits
5. **split_detector.py** — detección de gastos compartidos
6. **dashboard.py** — métricas y gráficos Plotly
7. **Tests unitarios** — empezar por `email_parser.py` y `deduplicator.py`
8. **Deploy** — Streamlit Cloud + README con screenshots

---

*Última actualización: 2026-05-26*
