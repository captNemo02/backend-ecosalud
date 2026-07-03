from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class Paciente(Base):
    __tablename__ = "pacientes"
    __table_args__ = {'schema': 'pacientes'}

    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    tipo_documento = Column(String(20), nullable=False)
    numero_documento = Column(String(20), unique=True, index=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(String(20))
    telefono = Column(String(20))
    email = Column(String(100), unique=True, index=True)
    direccion = Column(Text)
    estado = Column(String(20), default="ACTIVO")
    fecha_registro = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    mfa_code = Column(String(6), nullable=True)
    mfa_code_expires_at = Column(DateTime, nullable=True)

    historiales_clinicos = relationship("HistorialClinico", back_populates="paciente")
    recetas = relationship("Receta", back_populates="paciente")
    ordenes_medicas = relationship("OrdenMedica", back_populates="paciente")


class HistorialClinico(Base):
    __tablename__ = "historial_clinico"
    __table_args__ = {'schema': 'pacientes'}

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.pacientes.id"), nullable=False)
    tipo_registro = Column(String(50))
    titulo = Column(String(200))
    descripcion = Column(Text)
    fecha_evento = Column(Date)
    medico_responsable = Column(String(200))
    documento_adjunto_url = Column(Text)
    creado_en = Column(DateTime, server_default=func.now())

    paciente = relationship("Paciente", back_populates="historiales_clinicos")


class Receta(Base):
    __tablename__ = "recetas"
    __table_args__ = {'schema': 'pacientes'}

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.pacientes.id"), nullable=False)
    doctor_id = Column(Integer)
    orden_medica_id = Column(Integer)
    medicamento = Column(String(150), nullable=False)
    dosis = Column(String(100))
    duracion = Column(String(100))
    indicaciones = Column(Text)
    fecha_emision = Column(Date, server_default=func.current_date())
    fecha_vencimiento = Column(Date)
    estado = Column(String(30), default="VIGENTE")
    creado_en = Column(DateTime, server_default=func.now())

    paciente = relationship("Paciente", back_populates="recetas")


class OrdenMedica(Base):
    __tablename__ = "ordenes_medicas"
    __table_args__ = {'schema': 'pacientes'}

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.pacientes.id"), nullable=False)
    tipo_orden = Column(String(50), nullable=False)  # LABORATORIO, IMAGENOLOGIA, ESPECIALISTA, PROCEDIMIENTO
    descripcion = Column(Text, nullable=False)
    medico_responsable = Column(String(200), nullable=False)
    fecha_emision = Column(Date, server_default=func.current_date())
    fecha_vencimiento = Column(Date, nullable=True)
    estado = Column(String(30), default="ACTIVA")
    creado_en = Column(DateTime, server_default=func.now())

    paciente = relationship("Paciente", back_populates="ordenes_medicas")

