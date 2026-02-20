# Información del Modelo Usado

## Elección

- **Categoría:** Privado
- **Proveedor/Plataforma:** Anthropic
- **Modelo:** claude-sonnet-4-6
- **Fecha de acceso:** 2025-02-19

## Justificación

Claude claude-sonnet-4-6 ofrece la mejor relación entre capacidad de comprensión semántica y costo para tareas de extracción estructurada. Su soporte nativo de **tool calling** permite definir un schema explícito que el modelo debe respetar, eliminando la necesidad de parsear texto libre y reduciendo drásticamente los errores de formato. Para el tipo de documentos del challenge (minutas, notas, textos semiestructurados en español), Claude demuestra comprensión contextual superior a modelos más pequeños.

## Alternativas consideradas

| Modelo | Categoría | Razón por la que no se eligió |
|--------|-----------|-------------------------------|
| GROQ llama-3.1-70b | Gratis/Freemium | Tool calling menos robusto; mayor variabilidad en textos ambiguos |
| GPT-4o-mini | Privado | Capacidades similares pero requiere cuenta OpenAI adicional |
| Gemini 2.5 Flash | Privado | Buena opción alternativa; Claude tiene mejor soporte de español rioplatense |
| Ollama (local) | Open Source | Sin GPU RTX 3060+; latencia inaceptable en CPU |

## Configuración utilizada

- **Temperatura:** 0.1 (baja, para maximizar consistencia en extracción estructurada)
- **Max tokens:** 2048 (suficiente para el schema de salida; documentos muy largos se resumen en el prompt)
- **Tool choice:** `any` (fuerza invocación del tool, no permite respuesta libre)
