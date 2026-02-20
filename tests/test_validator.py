"""Tests unitarios para la capa de validación."""

import pytest
from src.validator import (
    validate_and_warn,
    _normalize_string,
    _normalize_list,
    _normalize_dict,
    _text_has_numbers,
    _text_suggests_actions,
)


class TestNormalizers:
    def test_normalize_string_strips_whitespace(self):
        assert _normalize_string("  hola  ") == "hola"

    def test_normalize_string_handles_non_string(self):
        assert _normalize_string(42) == "42"
        assert _normalize_string(None) == ""

    def test_normalize_list_filters_empty(self):
        assert _normalize_list(["a", "", "  ", "b"]) == ["a", "b"]

    def test_normalize_list_handles_non_list(self):
        assert _normalize_list(None) == []
        assert _normalize_list("texto") == []

    def test_normalize_dict_converts_values(self):
        result = _normalize_dict({"clave": 123, "otra": "valor"})
        assert result == {"clave": "123", "otra": "valor"}

    def test_normalize_dict_filters_none_values(self):
        result = _normalize_dict({"a": None, "b": "ok"})
        assert "a" not in result
        assert result["b"] == "ok"


class TestHeuristics:
    def test_detects_numbers_in_text(self):
        assert _text_has_numbers("el presupuesto es $1200")
        assert _text_has_numbers("tenemos 50 usuarios")
        assert not _text_has_numbers("no hay cifras aquí")

    def test_detects_action_keywords(self):
        assert _text_suggests_actions("hay que revisar el contrato")
        assert _text_suggests_actions("pendiente: definir arquitectura")
        assert not _text_suggests_actions("el sistema funciona bien")


class TestValidateAndWarn:
    def _raw(self, **overrides) -> dict:
        base = {
            "titulo": "Minuta de Arquitectura",
            "resumen": "Se discutió la arquitectura del nuevo sistema de recomendaciones con el equipo técnico.",
            "entidades_clave": ["FastAPI", "Pinecone"],
            "conceptos_principales": ["embeddings", "caché"],
            "datos_relevantes": {"presupuesto": "$1200/mes"},
            "acciones_sugeridas": ["Configurar Pinecone (Juan)"],
        }
        base.update(overrides)
        return base

    def test_valid_input_no_warnings(self):
        output, warnings = validate_and_warn(self._raw(), "texto de prueba")
        assert warnings == []
        assert output.titulo == "Minuta de Arquitectura"

    def test_empty_titulo_generates_warning(self):
        _, warnings = validate_and_warn(self._raw(titulo=""), "texto")
        assert any("titulo" in w for w in warnings)

    def test_generic_titulo_generates_warning(self):
        _, warnings = validate_and_warn(self._raw(titulo="Documento"), "texto largo sin más info")
        assert any("genérico" in w for w in warnings)

    def test_short_resumen_generates_warning(self):
        _, warnings = validate_and_warn(self._raw(resumen="Muy corto."), "texto")
        assert any("resumen" in w for w in warnings)

    def test_empty_entidades_generates_warning(self):
        _, warnings = validate_and_warn(self._raw(entidades_clave=[]), "texto")
        assert any("entidades_clave" in w for w in warnings)

    def test_empty_conceptos_generates_warning(self):
        _, warnings = validate_and_warn(self._raw(conceptos_principales=[]), "texto")
        assert any("conceptos_principales" in w for w in warnings)

    def test_missing_datos_with_numbers_generates_warning(self):
        _, warnings = validate_and_warn(
            self._raw(datos_relevantes={}),
            "el costo es $500 y tenemos 200 usuarios",
        )
        assert any("datos_relevantes" in w for w in warnings)

    def test_missing_acciones_with_action_keywords_generates_warning(self):
        _, warnings = validate_and_warn(
            self._raw(acciones_sugeridas=[]),
            "hay que revisar el sistema urgente",
        )
        assert any("acciones_sugeridas" in w for w in warnings)

    def test_empty_titulo_defaults_to_sin_titulo(self):
        output, _ = validate_and_warn(self._raw(titulo=""), "texto")
        assert output.titulo == "Sin título"

    def test_multiple_warnings_accumulate(self):
        raw = self._raw(titulo="", resumen="Corto.", entidades_clave=[])
        _, warnings = validate_and_warn(raw, "texto sin números ni acciones")
        assert len(warnings) >= 3
