SYSTEM_PROMPT = """\
Sos un sistema experto en análisis y estructuración de documentos en español e inglés.
Tu tarea es extraer información estructurada de textos libres: minutas, notas, resúmenes,
emails, reportes, etc.

INSTRUCCIONES:
1. Analizá el texto en detalle antes de extraer información.
2. Llamá SIEMPRE a la función `extract_document_structure` con los datos extraídos.
3. Para campos con información faltante o ambigua, completá con lo que puedas inferir del contexto.
4. Si no hay datos para un campo, devolvé array/objeto vacío (no null, no texto inventado).
5. El resumen debe capturar la idea central, no ser una copia del texto.
6. Las acciones sugeridas deben ser concretas, con responsable si está mencionado.
"""


def build_user_prompt(text: str) -> str:
    return f"""\
Analizá el siguiente texto y extraé su estructura usando la función disponible.

TEXTO:
---
{text}
---
"""


# Tool definition para Anthropic tool calling
EXTRACTION_TOOL: dict = {
    "name": "extract_document_structure",
    "description": (
        "Extrae información estructurada de un documento o texto libre. "
        "Llamar siempre con todos los campos requeridos."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "titulo": {
                "type": "string",
                "description": "Título descriptivo del documento (máx. 100 caracteres)",
            },
            "resumen": {
                "type": "string",
                "description": "Resumen conciso del contenido principal (2-4 oraciones)",
            },
            "entidades_clave": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Personas, sistemas, organizaciones o tecnologías mencionadas. "
                    "Formato: nombre tal como aparece en el texto."
                ),
            },
            "conceptos_principales": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ideas o temas centrales del texto",
            },
            "datos_relevantes": {
                "type": "object",
                "description": (
                    "Datos numéricos, fechas, métricas u otra información factual clave. "
                    "Claves descriptivas en español, valores como strings."
                ),
                "additionalProperties": {"type": "string"},
            },
            "acciones_sugeridas": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Tareas, decisiones o próximos pasos identificados. "
                    "Incluir responsable si está mencionado, ej: 'Revisar propuesta (Juan)'."
                ),
            },
        },
        "required": [
            "titulo",
            "resumen",
            "entidades_clave",
            "conceptos_principales",
            "datos_relevantes",
            "acciones_sugeridas",
        ],
    },
}
