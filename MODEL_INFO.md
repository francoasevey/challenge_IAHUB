# Información del Modelo Usado

## Elección

- **Categoría:** Privado
- **Proveedor/Plataforma:** Anthropic
- **Modelo:** claude-sonnet-4-6
- **Fecha de acceso:** 2025-02-19

## Justificación

Claude claude-sonnet-4-6 ofrece la mejor relación entre capacidad de comprensión semántica y costo para tareas de extracción estructurada. Su soporte nativo de **tool calling** permite definir un schema explícito que el modelo debe respetar, eliminando la necesidad de parsear texto libre y reduciendo drásticamente los errores de formato. Para el tipo de documentos del challenge (minutas, notas, textos semiestructurados en español), Claude demuestra comprensión contextual superior a modelos más pequeños.

## Alternativas consideradas

| Modelo | Categoría | Soporte PDF nativo | Costo input/1M tokens | Razón por la que no se eligió |
|--------|-----------|-------------------|----------------------|-------------------------------|
| GROQ llama-3.1-70b | Gratis/Freemium | No | $0.059 | No soporta PDF nativo; tool calling menos robusto y mayor variabilidad en textos ambiguos |
| GPT-4o | Privado | Sí | $2.50 | Capacidades similares a Claude pero requiere cuenta OpenAI adicional |
| GPT-4o-mini | Privado | Sí | $0.15 | Menor capacidad de inferencia en textos ambiguos o ruidosos |
| Gemini 2.5 Flash | Privado | Sí | $0.15 | La opción más económica con soporte PDF; descartada para este challenge por menor robustez en español rioplatense, pero es la **recomendada para producción a escala** |
| Ollama local (Llama, Mistral) | Open Source | No | $0 (self-hosted) | Sin GPU RTX 3060+; latencia inaceptable en CPU para uso en tiempo real |
| OCR Dolphin | Open Source | Sí (especializado) | $0 (self-hosted) | Especializado en extracción de texto desde imágenes/scans; el input del challenge ya es texto plano, no imágenes |

## Análisis de costos en producción

Para un sistema que procese **10.000 documentos por mes** (estimado ~2.000 tokens de input + 500 tokens de output por documento):

| Modelo | Costo mensual estimado | Observaciones |
|--------|----------------------|---------------|
| GROQ llama-3.1-70b | ~$3 | Requiere librería de extracción de texto para PDFs |
| **Gemini 2.5 Flash** | **~$10** | **Mejor relación costo/calidad para producción** |
| GPT-4o-mini | ~$35 | Buena calidad, costo intermedio |
| Claude Sonnet (este proyecto) | ~$200 | Máxima calidad y robustez; justificado para volúmenes bajos o documentos críticos |
| GPT-4o | ~$250 | Similar a Claude Sonnet |

**Conclusión para producción:** Para un escenario empresarial de alto volumen, **Gemini 2.5 Flash** es la opción óptima: soporta PDFs nativamente, tiene contexto de 1 millón de tokens (documentos muy largos sin problema), y es 20x más barato que Claude Sonnet manteniendo calidad comparable en extracción estructurada. Claude Sonnet se justifica cuando la precisión es crítica y el volumen es bajo.

## Configuración utilizada

- **Temperatura:** 0.1 (baja, para maximizar consistencia en extracción estructurada)
- **Max tokens:** 2048 (suficiente para el schema de salida; documentos muy largos se resumen en el prompt)
- **Tool choice:** `any` (fuerza invocación del tool, no permite respuesta libre)
