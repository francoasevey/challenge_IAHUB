"""Orquestación principal: texto/PDF → LLM → validación → resultado estructurado."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from .llm_client import LLMClient
from .schemas import ExtractionResult, Metadata
from .validator import validate_and_warn

logger = logging.getLogger(__name__)

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
        """Transforma texto libre en un ExtractionResult estructurado y validado."""
        if not text or not text.strip():
            raise ValueError("El texto de entrada no puede estar vacío.")

        logger.info("Extrayendo desde texto (%d caracteres)", len(text))
        raw = self.llm.extract(text)
        output, warnings = validate_and_warn(raw, text)

        if warnings:
            logger.warning("Warnings generados: %s", warnings)

        return ExtractionResult(
            input_original=text,
            output_estructurado=output,
            warnings=warnings,
            metadata=Metadata(
                modelo=self.model,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )

    def extract_from_pdf(self, pdf_path: str) -> ExtractionResult:
        """
        Procesa un PDF directamente usando la capacidad nativa de Claude.
        No requiere librerías de extracción de texto: Claude lee el PDF completo,
        incluyendo tablas, layout y formato.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"El archivo no es un PDF: {pdf_path}")

        logger.info("Extrayendo desde PDF: %s", pdf_path)
        raw = self.llm.extract_pdf(pdf_path)
        label = f"[PDF: {path.name}]"
        output, warnings = validate_and_warn(raw, label)

        if warnings:
            logger.warning("Warnings generados: %s", warnings)

        return ExtractionResult(
            input_original=label,
            output_estructurado=output,
            warnings=warnings,
            metadata=Metadata(
                modelo=self.model,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )
