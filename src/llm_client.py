"""Capa de interacción con el LLM (Anthropic Claude)."""

import time
import anthropic
from anthropic import APIError, APITimeoutError, RateLimitError
from typing import Any

from .prompts import SYSTEM_PROMPT, EXTRACTION_TOOL, build_user_prompt

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
        Envía el texto al LLM y retorna los datos extraídos via tool calling.

        Reintentos con backoff exponencial ante errores transitorios (timeout,
        rate limit). Falla rápido ante errores de autenticación o respuestas
        sin tool call.
        """
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                return self._call(text)
            except (APITimeoutError, RateLimitError) as exc:
                last_error = exc
                wait = 2**attempt
                print(
                    f"[llm_client] Intento {attempt + 1}/{max_retries} fallido "
                    f"({type(exc).__name__}). Reintentando en {wait}s..."
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

    def _call(self, text: str) -> dict[str, Any]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(text)}],
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "any"},  # Forzar uso de tool
        )

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
