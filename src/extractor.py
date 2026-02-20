"""Orquestación principal: texto → LLM → validación → resultado estructurado."""

from datetime import datetime, timezone

from .llm_client import LLMClient
from .schemas import ExtractionResult, Metadata
from .validator import validate_and_warn

DEFAULT_MODEL = "claude-sonnet-4-6"


class DocumentExtractor:
    """
    Punto de entrada para la extracción de documentos.

    Separa claramente:
      1. Interacción con LLM  → LLMClient
      2. Validación/normalización → validate_and_warn
      3. Serialización del resultado → ExtractionResult (Pydantic)
    """

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self.llm = LLMClient(api_key=api_key, model=model)
        self.model = model

    def extract(self, text: str) -> ExtractionResult:
        """
        Transforma texto libre en un ExtractionResult estructurado y validado.

        Args:
            text: Texto libre a analizar (minuta, nota, resumen, etc.)

        Returns:
            ExtractionResult con los datos extraídos, warnings y metadata.

        Raises:
            LLMError: Si el LLM falla luego de todos los reintentos.
            ValueError: Si el texto está vacío.
        """
        if not text or not text.strip():
            raise ValueError("El texto de entrada no puede estar vacío.")

        raw = self.llm.extract(text)
        output, warnings = validate_and_warn(raw, text)

        return ExtractionResult(
            input_original=text,
            output_estructurado=output,
            warnings=warnings,
            metadata=Metadata(
                modelo=self.model,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )
