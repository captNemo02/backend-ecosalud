from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import date

class ProcedimientoBase(BaseModel):
    cita_id: Optional[int] = Field(None, description="ID de la cita médica asociada, si aplica")
    paciente_id: int = Field(..., description="ID del paciente asociado al procedimiento")
    clinica_id: int = Field(..., description="ID de la clínica donde se realiza")
    nombre_procedimiento: str = Field(..., max_length=150, description="Nombre del procedimiento quirúrgico o examen")
    descripcion: Optional[str] = Field(None, description="Breve descripción del procedimiento")
    fecha_realizacion: Optional[date] = Field(None, description="Fecha de realización")
    costo: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2, description="Costo asociado para facturación")
    estado: Optional[str] = Field("PROGRAMADO", max_length=30, description="Estado del procedimiento")
    notas: Optional[str] = Field(None, description="Notas adicionales o comentarios médicos")

class ProcedimientoCreate(ProcedimientoBase):
    pass

class ProcedimientoResponse(ProcedimientoBase):
    id: int

    class Config:
        from_attributes = True

# --- Nuevos Esquemas Dinámicos ---
from datetime import datetime

class SedeBase(BaseModel):
    clinica_id: int
    nombre_sede: str
    direccion: str
    telefono: Optional[str] = None
    horario_atencion: Optional[str] = None
    activo: Optional[bool] = True

class SedeResponse(SedeBase):
    id: int

    class Config:
        from_attributes = True


class CitaBase(BaseModel):
    clinica_id: int
    sede_id: int
    paciente_id: int
    doctor_id: int
    fecha_hora: datetime
    duracion_minutos: Optional[int] = 30
    motivo: Optional[str] = None
    estado: Optional[str] = "AGENDADA"
    notas_medicas: Optional[str] = None
    creado_en: Optional[datetime] = None

class CitaResponse(CitaBase):
    id: int

    class Config:
        from_attributes = True


class CitaCreate(BaseModel):
    clinica_id: int
    sede_id: int
    paciente_id: int
    doctor_id: int
    fecha_hora: datetime
    duracion_minutos: Optional[int] = 30
    motivo: Optional[str] = None
    estado: Optional[str] = "AGENDADA"
    notas_medicas: Optional[str] = None

