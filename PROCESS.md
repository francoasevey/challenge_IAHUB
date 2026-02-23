# Proceso de Desarrollo

## Herramientas de IA Usadas

- [x] Claude (Claude Code — asistente de implementación)

---

## Mi Flujo de Trabajo

### 1. Planificación

Empecé leyendo el challenge completo e identificando los tres ejes de evaluación (IA estratégica 40%, calidad técnica 30%, documentación 30%). Antes de escribir código, diseñé el schema de salida y la arquitectura en tres capas, para tener claro qué responsabilidad tenía cada módulo. Elegí la Opción C (documentos) por ser la más versátil y representativa del trabajo real del equipo.

La primera decisión técnica fue usar **tool calling** en lugar de prompt engineering puro. Esto garantiza que el LLM siempre devuelva la estructura esperada, sin necesidad de parsear texto libre ni depender de instrucciones en el prompt para el formato.

### 2. Prompts que me funcionaron

**System prompt** — clave fue ser directivo sin ser verboso:
```
Sos un sistema experto en análisis y estructuración de documentos en español e inglés.
[...]
Llamá SIEMPRE a la función `extract_document_structure` con los datos extraídos.
Para campos con información faltante o ambigua, completá con lo que puedas inferir del contexto.
Si no hay datos para un campo, devolvé array/objeto vacío (no null, no texto inventado).
```

Lo importante: indicar explícitamente qué hacer cuando falta información (vacío, no null, no inventar). Esto reduce alucinaciones en campos opcionales.

**Tool definition** — describir cada campo con ejemplos concretos fue lo que más mejoró la calidad:
- En lugar de "lista de entidades", usar: "Personas, sistemas, organizaciones o tecnologías mencionadas. Formato: nombre tal como aparece en el texto."
- En `acciones_sugeridas`: "Incluir responsable si está mencionado, ej: 'Revisar propuesta (Juan)'."

### 3. Partes donde IA me ayudó

- **Estructura base del proyecto:** Claude Code generó el scaffolding inicial (schemas, prompts, llm_client, validator, extractor, main).
- **Tests:** generados con casos edge que yo definí (texto vacío, warnings múltiples, LLM mockeado).
- **Heurísticas del validator:** las regex para detectar números y keywords de acción fueron sugeridas y luego ajustadas.

Lo que revisé y modifiqué manualmente:
- El wording del system prompt (varias iteraciones para equilibrar precisión e inferencia en textos ambiguos).
- Los umbrales de warnings (MIN_RESUMEN_WORDS = 10, GENERIC_TITLES).
- Los 3 inputs de prueba, diseñados deliberadamente para testear los tres escenarios del challenge.

### 4. Decisiones Técnicas

| Decisión | ¿Con ayuda de IA? | Justificación |
|----------|-------------------|---------------|
| Tool calling sobre prompt engineering | No (criterio propio) | Más robusto: el formato está garantizado por el protocolo, no por el prompt |
| Temperatura 0.1 | No | Extracción estructurada no se beneficia de creatividad; consistencia > diversidad |
| Pydantic v2 para validación con JSON Schema | Sí (sugerido) | Pydantic v2 está construido sobre JSON Schema — valida tipos, estructura y campos obligatorios. Cumple el bonus "Validación con JSON Schema" sin necesidad de un archivo `.json` separado. El schema puede exportarse en cualquier momento con `ExtractionResult.model_json_schema()` |
| Backoff exponencial en reintentos | Sí (implementación) | Patrón estándar para rate limits; definí los parámetros (3 intentos, 2^n segundos) |
| Separación validator / llm_client | No (criterio propio) | Permite testear la validación sin llamadas reales al LLM |
| Warnings no bloquean extracción | No (criterio propio) | Un texto ambiguo sigue produciendo valor parcial; el warning informa al caller |

### 5. Desafíos Encontrados

**Textos ambiguos (caso `ambiguous.txt`):** el LLM tiende a inventar datos cuando la información no está clara. La solución fue ser explícito en el prompt: "si no hay datos, devolvé vacío". Combinado con la capa de validación que detecta estos casos y los marca en `warnings`, el sistema es honesto sobre su incertidumbre en lugar de silenciar el problema.

**Definir qué es un "warning":** el límite entre "dato que falta" y "texto genuinamente sin esa información" es difuso. Opté por heurísticas simples (longitud del resumen, presencia de números en el texto original vs. datos_relevantes vacío) que son explicables y ajustables.

**Tool calling con `tool_choice: any`:** inicialmente usé `auto`, lo que permitía al modelo responder en texto libre en algunos casos. Cambiarlo a `any` fuerza siempre el uso del tool.

### 6. Qué haría diferente

- **Exportar JSON Schema como artefacto:** Pydantic v2 ya valida con JSON Schema internamente. Como mejora, exportaría el schema como archivo `.json` con `ExtractionResult.model_json_schema()` para que otros sistemas o equipos (Java, Go, frontend) puedan validar el output sin depender de Python.
- **Logging estructurado:** en producción agregaría logs con el tiempo de cada llamada al LLM, warnings generados y tokens usados, para monitorear calidad a lo largo del tiempo.
- **Evaluación automatizada:** diseñar un conjunto de inputs con outputs esperados para medir precisión del extractor ante cambios de modelo o prompt.
- **Batching:** para escalar, aprovechar la Batches API de Anthropic (50% más barato, hasta 24h de latencia) para procesar miles de documentos offline.
- **Cambio de modelo para producción a escala:** para un sistema empresarial con alto volumen, migraría a **Gemini 2.5 Flash** que soporta PDFs nativamente y cuesta ~20x menos que Claude Sonnet manteniendo calidad comparable. La arquitectura en capas del proyecto facilita este cambio: solo se modifica `llm_client.py`.

### 7. Decisión de modelo: prototipo vs. producción

Una reflexión importante sobre la elección del modelo:

| Contexto | Modelo recomendado | Justificación |
|----------|--------------------|---------------|
| **Este challenge / prototipo** | Claude Sonnet | Máxima robustez, tool calling nativo, excelente en español; el costo es irrelevante a escala de prueba |
| **Producción < 5.000 docs/mes** | Claude Sonnet o GPT-4o | Calidad crítica, volumen manejable |
| **Producción > 5.000 docs/mes** | Gemini 2.5 Flash | $10/mes vs $200/mes; soporta PDF nativo; contexto de 1M tokens |
| **Volumen masivo + bajo costo** | GROQ + pdfplumber | Casi gratuito; requiere librería adicional para PDFs; menor consistencia |

La arquitectura del proyecto fue diseñada para que este cambio sea transparente al resto del sistema: `extractor.py`, `validator.py` y `schemas.py` no saben qué modelo se usa.
