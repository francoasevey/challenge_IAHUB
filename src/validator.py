"""Capa de validación y normalización del output del LLM."""

import re
from typing import Any

from .schemas import OutputEstructurado

# Umbrales para detección de baja confianza
MIN_RESUMEN_WORDS = 10
MIN_TITULO_CHARS = 3
GENERIC_TITLES = {"documento", "texto", "resumen", "reunión", "meeting", "nota"}


def validate_and_warn(
    raw: dict[str, Any], original_text: str
) -> tuple[OutputEstructurado, list[str]]:
    """
    Valida y normaliza los datos crudos del LLM.

    Retorna (OutputEstructurado validado, lista de warnings).
    Los warnings indican campos ausentes, ambiguos o de baja confianza,
    pero no bloquean la extracción.
    """
    warnings: list[str] = []

    titulo = _normalize_string(raw.get("titulo", ""))
    resumen = _normalize_string(raw.get("resumen", ""))
    entidades = _normalize_list(raw.get("entidades_clave", []))
    conceptos = _normalize_list(raw.get("conceptos_principales", []))
    datos = _normalize_dict(raw.get("datos_relevantes", {}))
    acciones = _normalize_list(raw.get("acciones_sugeridas", []))

    # — Validaciones de baja confianza —

    if len(titulo) < MIN_TITULO_CHARS:
        warnings.append("titulo: no se pudo extraer un título descriptivo del texto.")
    elif titulo.lower() in GENERIC_TITLES:
        warnings.append(
            f"titulo: el título '{titulo}' es genérico; podría no representar bien el contenido."
        )

    if len(resumen.split()) < MIN_RESUMEN_WORDS:
        warnings.append(
            "resumen: el resumen es muy corto; el texto puede no tener contenido suficiente."
        )

    if not entidades:
        warnings.append(
            "entidades_clave: no se identificaron entidades. El texto puede carecer de referencias específicas."
        )

    if not conceptos:
        warnings.append(
            "conceptos_principales: no se identificaron conceptos. El texto puede ser muy vago."
        )

    if not datos and _text_has_numbers(original_text):
        warnings.append(
            "datos_relevantes: el texto contiene números pero no se extrajeron datos relevantes."
        )

    if not acciones and _text_suggests_actions(original_text):
        warnings.append(
            "acciones_sugeridas: el texto parece contener tareas o decisiones que no fueron capturadas."
        )

    output = OutputEstructurado(
        titulo=titulo or "Sin título",
        resumen=resumen or "Sin resumen disponible.",
        entidades_clave=entidades,
        conceptos_principales=conceptos,
        datos_relevantes=datos,
        acciones_sugeridas=acciones,
    )

    return output, warnings


# — Normalizadores —


def _normalize_string(value: Any) -> str:
    if not isinstance(value, str):
        return str(value) if value is not None else ""
    return value.strip()


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if item and str(item).strip()]


def _normalize_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(k).strip(): str(v).strip()
        for k, v in value.items()
        if k and v is not None
    }


# — Heurísticas para detección de baja confianza —

_NUMBER_PATTERN = re.compile(r"\b\d+[\.,]?\d*\s*(%|hs?|min|kg|km|USD|ARS|€|\$)?")
_ACTION_KEYWORDS = re.compile(
    r"\b(hay que|se debe|pendiente|tarea|acción|próximo paso|next step|"
    r"to-do|TODO|asignar|revisar|implementar|definir|preparar|analizar)\b",
    re.IGNORECASE,
)


def _text_has_numbers(text: str) -> bool:
    return bool(_NUMBER_PATTERN.search(text))


def _text_suggests_actions(text: str) -> bool:
    return bool(_ACTION_KEYWORDS.search(text))
