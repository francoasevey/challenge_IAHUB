from pydantic import BaseModel, Field
from typing import Any


class OutputEstructurado(BaseModel):
    titulo: str = Field(..., description="Título descriptivo del documento")
    resumen: str = Field(..., description="Resumen conciso del contenido principal")
    entidades_clave: list[str] = Field(
        default_factory=list,
        description="Personas, sistemas, organizaciones o tecnologías mencionadas",
    )
    conceptos_principales: list[str] = Field(
        default_factory=list,
        description="Ideas o temas centrales del texto",
    )
    datos_relevantes: dict[str, Any] = Field(
        default_factory=dict,
        description="Datos numéricos, fechas, métricas u otra información factual",
    )
    acciones_sugeridas: list[str] = Field(
        default_factory=list,
        description="Tareas, decisiones o próximos pasos identificados",
    )


class Metadata(BaseModel):
    modelo: str
    timestamp: str
    opcion: str = "C"


class ExtractionResult(BaseModel):
    input_original: str
    output_estructurado: OutputEstructurado
    warnings: list[str] = Field(default_factory=list)
    metadata: Metadata
