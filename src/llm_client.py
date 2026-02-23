"""Capa de interacción con el LLM (Anthropic Claude)."""

import base64
import logging
import time
import anthropic
from anthropic import APIError, APITimeoutError, RateLimitError
from typing import Any

from .prompts import SYSTEM_PROMPT, EXTRACTION_TOOL, build_user_prompt

logger = logging.getLogger(__name__)

# Temperatura baja para maximizar consistencia en extracción estructurada.
# Un valor de 0.1 reduce variabilidad sin perder capacidad de inferencia
# sobre textos ambiguos.
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 2048


class LLMError(Exception):
    """Error irrecuperable al llamar al LLM."""


class LLMClient:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def extract(self, text: str, max_retries: int = 3) -> dict[str, Any]:
        """
        Envía texto al LLM y retorna los datos extraídos via tool calling.

        Reintentos con backoff exponencial ante errores transitorios (timeout,
        rate limit). Falla rápido ante errores de autenticación o respuestas
        sin tool call.
        """
        logger.info("Iniciando extracción de texto (%d caracteres)", len(text))
        return self._call_with_retries(
            lambda: self._call_text(text), max_retries
        )

    def extract_pdf(self, pdf_path: str, max_retries: int = 3) -> dict[str, Any]:
        """
        Envía un PDF directamente al LLM sin extracción previa de texto.
        Claude lee el PDF de forma nativa (layout, tablas, formato).
        """
        logger.info("Iniciando extracción de PDF: %s", pdf_path)
        with open(pdf_path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
        return self._call_with_retries(
            lambda: self._call_pdf(pdf_data), max_retries
        )

    def _call_with_retries(self, call_fn, max_retries: int) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                result = call_fn()
                logger.info("Extracción exitosa en intento %d", attempt + 1)
                return result
            except (APITimeoutError, RateLimitError) as exc:
                last_error = exc
                wait = 2**attempt
                logger.warning(
                    "Intento %d/%d fallido (%s). Reintentando en %ds...",
                    attempt + 1, max_retries, type(exc).__name__, wait,
                )
                time.sleep(wait)
            except LLMError:
                raise
            except APIError as exc:
                raise LLMError(f"Error de API no recuperable: {exc}") from exc

        raise LLMError(
            f"El LLM no respondió correctamente luego de {max_retries} intentos. "
            f"Último error: {last_error}"
        )

    def _call_text(self, text: str) -> dict[str, Any]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(text)}],
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "any"},
        )
        return self._extract_tool_result(response)

    def _call_pdf(self, pdf_data: str) -> dict[str, Any]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Analizá este documento y extraé su estructura usando la función disponible.",
                    },
                ],
            }],
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "any"},
        )
        return self._extract_tool_result(response)

    def _extract_tool_result(self, response) -> dict[str, Any]:
        for block in response.content:
            if (
                block.type == "tool_use"
                and block.name == "extract_document_structure"
            ):
                return block.input  # type: ignore[return-value]

        raise LLMError(
            "El modelo no invocó `extract_document_structure`. "
            f"Respuesta: {response.content}"
        )
