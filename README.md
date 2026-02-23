# Extractor de Documentos — Challenge IA Hub

Sistema que transforma texto libre (minutas, notas, resúmenes) en JSON estructurado, usando la API de Claude con **tool calling** para garantizar output consistente.

**Opción elegida: C — Documento / Texto General**

---

## Arquitectura

```
Texto libre
    │
    ▼
┌─────────────────┐
│   LLMClient     │  ← src/llm_client.py  (interacción con Anthropic)
│  tool calling   │
└────────┬────────┘
         │ dict crudo
         ▼
┌─────────────────┐
│   validator     │  ← src/validator.py   (validación + warnings)
└────────┬────────┘
         │ OutputEstructurado + warnings
         ▼
┌─────────────────┐
│ ExtractionResult│  ← src/schemas.py     (serialización Pydantic → JSON)
└─────────────────┘
```

Separación de responsabilidades en tres capas:
1. **LLMClient** — solo habla con la API, con reintentos ante errores transitorios
2. **validator** — normaliza y genera warnings independientemente del LLM
3. **schemas (Pydantic)** — garantiza tipos y serialización correcta

---

## Instalación

**Requisitos:** Python 3.11+

```bash
# Clonar y entrar al directorio
git clone <repo-url>
cd challenge_IAHUB

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
cp .env.example .env
# Editar .env y completar ANTHROPIC_API_KEY
```

---

## Uso

### Texto directo
```bash
python main.py --text "Reunión del 10/02: se decidió migrar a FastAPI. Juan se encarga del deploy."
```

### Desde archivo
```bash
python main.py --file inputs/ideal.txt
```

### Guardar resultado en archivo
```bash
python main.py --file inputs/ideal.txt --output resultado.json
```

### Generar todos los outputs de prueba
```bash
python generate_outputs.py
# Genera outputs.json con los 3 casos
```

---

## Ejemplo de salida

```bash
python main.py --file inputs/ideal.txt
```

```json
{
  "input_original": "Minuta de Reunión — Revisión de Arquitectura...",
  "output_estructurado": {
    "titulo": "Revisión de Arquitectura del Sistema de Recomendaciones",
    "resumen": "Se acordó una arquitectura híbrida con Pinecone como vector DB y FastAPI para la API de recomendaciones, con Redis como caché.",
    "entidades_clave": ["Lucía Fernández", "Matías Gómez", "Ana Torres", "Rodrigo Paz", "Pinecone", "FastAPI", "Redis", "OpenAI"],
    "conceptos_principales": ["filtrado colaborativo", "embeddings", "vector database", "caché"],
    "datos_relevantes": {
      "presupuesto_pinecone": "$1.200 USD/mes",
      "latencia_pinecone": "p95 < 80ms",
      "costo_embeddings": "$0.13 por millón de tokens",
      "usuarios_activos": "50.000 diarios",
      "pico_requests": "800/segundo"
    },
    "acciones_sugeridas": [
      "Preparar dataset de entrenamiento con últimos 6 meses (Ana Torres, límite 21/02)",
      "Desarrollar endpoints base de FastAPI (Matías Gómez, límite 28/02)",
      "Provisionar infraestructura AWS (Rodrigo Paz, límite 24/02)",
      "Revisar y aprobar contrato de API (Lucía Fernández, límite 01/03)"
    ]
  },
  "warnings": [],
  "metadata": {
    "modelo": "claude-sonnet-4-6",
    "timestamp": "2025-02-14T18:30:00+00:00",
    "opcion": "C"
  }
}
```

---

## Docker

```bash
# Construir la imagen
docker build -t extractor-docs .

# Procesar un archivo
docker run --env-file .env -v $(pwd)/inputs:/app/inputs extractor-docs \
  python main.py --file inputs/ideal.txt

# Texto directo
docker run --env-file .env extractor-docs \
  python main.py --text "Reunión del lunes: se decidió migrar a FastAPI."

# Generar todos los outputs
docker run --env-file .env -v $(pwd)/inputs:/app/inputs -v $(pwd)/outputs:/app/outputs extractor-docs \
  python generate_outputs.py
```

O con docker-compose:

```bash
docker-compose run extractor python main.py --file inputs/ideal.txt
```

---

## Limitaciones conocidas

### Soporte PDF
El soporte de PDF usa la capacidad nativa de Claude (envío como base64). Funciona correctamente para documentos de uso habitual (minutas, reportes, contratos de pocas páginas). Para PDFs muy grandes (más de ~50 páginas o más de 20MB) puede exceder los límites de contexto del modelo o el tamaño máximo de request de la API. En ese caso, se recomienda dividir el documento o usar una librería de extracción de texto (`pdfplumber`) como preprocesamiento.

---

## Tests

```bash
pytest tests/ -v
```

---

## Decisiones Técnicas

| Decisión | Elección | Justificación |
|----------|----------|---------------|
| **LLM** | Claude claude-sonnet-4-6 | Mejor relación capacidad/costo para extracción estructurada; tool calling nativo garantiza formato |
| **Tool calling** | `tool_choice: any` | Fuerza estructura en lugar de depender de prompt engineering; más robusto que parsear texto libre |
| **Temperatura** | 0.1 | Maximiza consistencia en extracción estructurada, sin eliminar capacidad inferencial |
| **Validación** | Pydantic v2 | Tipos garantizados + serialización JSON sin código extra |
| **Reintentos** | Backoff exponencial (3 intentos) | Maneja rate limits y timeouts sin fallar ante errores transitorios |

### Temperatura

Se usa **0.1** (casi determinista). En extracción de datos la creatividad no aporta valor; queremos el mismo output para el mismo input. Un valor de 0 sería ideal pero puede generar loops en algunos modelos.

### Escalabilidad

Para escalar a miles de inputs diarios:
- **Cola de trabajo** (SQS/Celery) con workers paralelos
- **Caché** de resultados por hash del input (inputs repetidos son frecuentes en pipelines)
- **Batching** con Anthropic Batches API para reducir costo hasta 50%
- **Rate limiting** propio para no exceder cuotas del proveedor

### Fallos del proveedor

- Reintentos con backoff exponencial para errores transitorios (timeout, 429)
- Fallo rápido para errores permanentes (401, 400)
- Circuit breaker recomendado en producción (no implementado por scope del challenge)
