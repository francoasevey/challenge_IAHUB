#!/usr/bin/env python3
"""
Punto de entrada CLI para el extractor de documentos.

Uso:
    python main.py --text "Texto libre aquí..."
    python main.py --file inputs/ideal.txt
    python main.py --file inputs/ideal.txt --output resultado.json
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from src.extractor import DocumentExtractor
from src.llm_client import LLMError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrae información estructurada de documentos usando Claude."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Texto directo a procesar")
    group.add_argument("--file", type=str, help="Ruta al archivo .txt a procesar")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Ruta del archivo JSON de salida (opcional; por defecto imprime en stdout)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-6",
        help="Modelo Claude a usar (default: claude-sonnet-4-6)",
    )
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    try:
        with open(args.file, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{args.file}'", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: la variable de entorno ANTHROPIC_API_KEY no está definida.\n"
            "Copiá .env.example a .env y completá tu API key.",
            file=sys.stderr,
        )
        sys.exit(1)

    args = parse_args()
    text = load_text(args)

    extractor = DocumentExtractor(api_key=api_key, model=args.model)

    try:
        result = extractor.extract(text)
    except ValueError as exc:
        print(f"Error de input: {exc}", file=sys.stderr)
        sys.exit(1)
    except LLMError as exc:
        print(f"Error del LLM: {exc}", file=sys.stderr)
        sys.exit(1)

    output_json = json.dumps(result.model_dump(), indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Resultado guardado en '{args.output}'")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
