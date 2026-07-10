from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime

# --- Paciente Schemas ---
class PacienteBase(BaseModel):
    nombres: str
    apellidos: str
    tipo_documento: str
    numero_documento: str
    fecha_nacimiento: date
    genero: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    estado: Optional[str] = "ACTIVO"

class PacienteCreate(PacienteBase):
    password: str

class PacienteUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    estado: Optional[str] = None

class PacienteResponse(PacienteBase):
    id: int
    fecha_registro: datetime 
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True

# --- Historial Clinico Schemas ---
class HistorialClinicoBase(BaseModel):
    tipo_registro: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_evento: Optional[date] = None
    medico_responsable: Optional[str] = None
    documento_adjunto_url: Optional[str] = None

class HistorialClinicoCreate(HistorialClinicoBase):
    paciente_id: int

class HistorialClinicoResponse(HistorialClinicoBase):
    id: int
    paciente_id: int
    creado_en: datetime

    class Config:
        from_attributes = True

# --- Receta Schemas ---
class RecetaBase(BaseModel):
    doctor_id: Optional[int] = None
    orden_medica_id: Optional[int] = None
    medicamento: str
    dosis: Optional[str] = None
    duracion: Optional[str] = None
    indicaciones: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    estado: Optional[str] = "VIGENTE"

class RecetaCreate(RecetaBase):
    paciente_id: int

class RecetaResponse(RecetaBase):
    id: int
    paciente_id: int
    fecha_emision: date
    creado_en: datetime

    class Config:
        from_attributes = True


# --- Authentication Schemas ---
class PacienteLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    mfa_required: bool
    mfa_token: Optional[str] = None
    email: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    paciente_id: Optional[int] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    paciente_id: int
    nombres: str
    apellidos: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class MFAVerifyRequest(BaseModel):
    mfa_token: str
    code: str

class MFAResendRequest(BaseModel):
    mfa_token: str


# --- Orden Medica Schemas ---
class OrdenMedicaBase(BaseModel):
    paciente_id: int
    tipo_orden: str = Field(..., description="LABORATORIO, IMAGENOLOGIA, ESPECIALISTA, o PROCEDIMIENTO")
    descripcion: str
    medico_responsable: str
    fecha_vencimiento: Optional[date] = None
    estado: Optional[str] = "ACTIVA"

class OrdenMedicaCreate(OrdenMedicaBase):
    pass

class OrdenMedicaResponse(OrdenMedicaBase):
    id: int
    fecha_emision: date
    creado_en: datetime

    class Config:
        from_attributes = True

