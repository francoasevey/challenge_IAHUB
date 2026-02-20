#!/usr/bin/env python3
"""
Procesa los 3 inputs de prueba y genera outputs.json con todos los resultados.

Uso:
    python generate_outputs.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.extractor import DocumentExtractor
from src.llm_client import LLMError

INPUTS = {
    "caso_ideal": "inputs/ideal.txt",
    "caso_ambiguo": "inputs/ambiguous.txt",
    "caso_ruidoso": "inputs/noisy.txt",
}


def main() -> None:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY no definida.", file=sys.stderr)
        sys.exit(1)

    extractor = DocumentExtractor(api_key=api_key)
    results = {}

    for case_name, filepath in INPUTS.items():
        print(f"Procesando '{case_name}' ({filepath})...")
        try:
            text = Path(filepath).read_text(encoding="utf-8")
            result = extractor.extract(text)
            results[case_name] = result.model_dump()
            warnings = result.warnings
            print(f"  OK — {len(warnings)} warning(s): {warnings if warnings else 'ninguno'}")
        except FileNotFoundError:
            print(f"  ERROR: archivo '{filepath}' no encontrado.", file=sys.stderr)
            results[case_name] = {"error": f"Archivo no encontrado: {filepath}"}
        except LLMError as exc:
            print(f"  ERROR LLM: {exc}", file=sys.stderr)
            results[case_name] = {"error": str(exc)}

    output_path = Path("outputs.json")
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nOutputs guardados en '{output_path}'")


if __name__ == "__main__":
    main()
