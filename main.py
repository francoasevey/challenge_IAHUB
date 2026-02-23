#!/usr/bin/env python3
"""
Punto de entrada CLI para el extractor de documentos.

Uso:
    python main.py --text "Texto libre aquí..."
    python main.py --file inputs/ideal.txt
    python main.py --file informe.pdf
    python main.py --folder inputs/ --output outputs/batch.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.extractor import DocumentExtractor
from src.llm_client import LLMError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrae información estructurada de documentos usando Claude."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Texto directo a procesar")
    group.add_argument("--file", type=str, help="Ruta al archivo .txt o .pdf a procesar")
    group.add_argument("--folder", type=str, help="Carpeta con archivos .txt y .pdf a procesar en batch")
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


def process_single(extractor: DocumentExtractor, args: argparse.Namespace) -> dict:
    if args.text:
        logger.info("Modo: texto directo")
        result = extractor.extract(args.text)
    else:
        path = Path(args.file)
        if path.suffix.lower() == ".pdf":
            logger.info("Modo: archivo PDF — %s", path.name)
            result = extractor.extract_from_pdf(str(path))
        else:
            logger.info("Modo: archivo de texto — %s", path.name)
            try:
                text = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                logger.error("Archivo no encontrado: %s", args.file)
                sys.exit(1)
            result = extractor.extract(text)

    return result.model_dump()


def process_batch(extractor: DocumentExtractor, folder: str) -> dict:
    folder_path = Path(folder)
    if not folder_path.is_dir():
        logger.error("La carpeta no existe: %s", folder)
        sys.exit(1)

    files = sorted(
        [f for f in folder_path.iterdir() if f.suffix.lower() in (".txt", ".pdf")]
    )

    if not files:
        logger.warning("No se encontraron archivos .txt o .pdf en: %s", folder)
        return {}

    logger.info("Procesando %d archivos en batch desde '%s'", len(files), folder)
    results = {}

    for file in files:
        logger.info("→ Procesando: %s", file.name)
        try:
            if file.suffix.lower() == ".pdf":
                result = extractor.extract_from_pdf(str(file))
            else:
                result = extractor.extract(file.read_text(encoding="utf-8"))
            results[file.name] = result.model_dump()
            logger.info("  OK — %d warning(s)", len(result.warnings))
        except (LLMError, ValueError, FileNotFoundError) as exc:
            logger.error("  ERROR en %s: %s", file.name, exc)
            results[file.name] = {"error": str(exc)}

    return results


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error(
            "ANTHROPIC_API_KEY no definida. "
            "Copiá .env.example a .env y completá tu API key."
        )
        sys.exit(1)

    args = parse_args()
    extractor = DocumentExtractor(api_key=api_key, model=args.model)

    try:
        if args.folder:
            data = process_batch(extractor, args.folder)
        else:
            data = process_single(extractor, args)
    except (LLMError, ValueError) as exc:
        logger.error("Error durante la extracción: %s", exc)
        sys.exit(1)

    output_json = json.dumps(data, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        logger.info("Resultado guardado en '%s'", args.output)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
