"""Tests de integración del DocumentExtractor (con LLM mockeado)."""

from unittest.mock import MagicMock, patch
import pytest

from src.extractor import DocumentExtractor
from src.llm_client import LLMError


MOCK_LLM_RESPONSE = {
    "titulo": "Minuta de Arquitectura",
    "resumen": "Se acordó usar FastAPI con Pinecone como vector database para el sistema de recomendaciones.",
    "entidades_clave": ["FastAPI", "Pinecone", "Redis"],
    "conceptos_principales": ["embeddings", "filtrado colaborativo", "caché"],
    "datos_relevantes": {"presupuesto": "$1200/mes", "latencia_objetivo": "p95 < 80ms"},
    "acciones_sugeridas": [
        "Configurar Pinecone (Rodrigo)",
        "Preparar dataset (Ana)",
    ],
}


@pytest.fixture
def extractor():
    return DocumentExtractor(api_key="test-key-mock")


class TestDocumentExtractor:
    def test_extract_returns_valid_result(self, extractor):
        with patch.object(extractor.llm, "extract", return_value=MOCK_LLM_RESPONSE):
            result = extractor.extract("Texto de prueba de arquitectura con presupuesto $1200.")

        assert result.input_original.startswith("Texto")
        assert result.output_estructurado.titulo == "Minuta de Arquitectura"
        assert "FastAPI" in result.output_estructurado.entidades_clave
        assert result.metadata.modelo == "claude-sonnet-4-6"
        assert result.metadata.opcion == "C"

    def test_extract_includes_timestamp(self, extractor):
        with patch.object(extractor.llm, "extract", return_value=MOCK_LLM_RESPONSE):
            result = extractor.extract("Texto de prueba.")

        assert result.metadata.timestamp
        assert "T" in result.metadata.timestamp  # ISO format

    def test_extract_raises_on_empty_text(self, extractor):
        with pytest.raises(ValueError, match="vacío"):
            extractor.extract("")

    def test_extract_raises_on_whitespace_only(self, extractor):
        with pytest.raises(ValueError, match="vacío"):
            extractor.extract("   \n\t  ")

    def test_extract_propagates_llm_error(self, extractor):
        with patch.object(extractor.llm, "extract", side_effect=LLMError("timeout")):
            with pytest.raises(LLMError):
                extractor.extract("Texto válido.")

    def test_extract_result_is_serializable(self, extractor):
        import json
        with patch.object(extractor.llm, "extract", return_value=MOCK_LLM_RESPONSE):
            result = extractor.extract("Texto de prueba.")

        # Debe poder serializarse a JSON sin errores
        json_str = json.dumps(result.model_dump(), ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["output_estructurado"]["titulo"] == "Minuta de Arquitectura"

    def test_warnings_generated_for_incomplete_response(self, extractor):
        incomplete = {**MOCK_LLM_RESPONSE, "entidades_clave": [], "conceptos_principales": []}
        with patch.object(extractor.llm, "extract", return_value=incomplete):
            result = extractor.extract("Texto sin entidades claras.")

        assert len(result.warnings) > 0
