from sqlalchemy import Column, Integer, String, Text, Date, Numeric, Boolean, DateTime, func
from app.database import Base

class Procedimiento(Base):
    __tablename__ = "procedimientos"
    __table_args__ = {'schema': 'clinicas'}

    id = Column(Integer, primary_key=True, index=True)
    cita_id = Column(Integer, nullable=True)
    paciente_id = Column(Integer, nullable=False)
    clinica_id = Column(Integer, nullable=False)
    nombre_procedimiento = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_realizacion = Column(Date, nullable=True)
    costo = Column(Numeric(12, 2), nullable=True)
    estado = Column(String(30), default="PROGRAMADO", nullable=False)
    notas = Column(Text, nullable=True)


class Sede(Base):
    __tablename__ = "sedes"
    __table_args__ = {'schema': 'clinicas'}

    id = Column(Integer, primary_key=True, index=True)
    clinica_id = Column(Integer, nullable=False)
    nombre_sede = Column(String(100), nullable=False)
    direccion = Column(Text, nullable=False)
    telefono = Column(String(20), nullable=True)
    horario_atencion = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)


class Cita(Base):
    __tablename__ = "citas"
    __table_args__ = {'schema': 'clinicas'}

    id = Column(Integer, primary_key=True, index=True)
    clinica_id = Column(Integer, nullable=False)
    sede_id = Column(Integer, nullable=False)
    paciente_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer, nullable=False)
    fecha_hora = Column(DateTime, nullable=False)
    duracion_minutos = Column(Integer, default=30, nullable=False)
    motivo = Column(String(200), nullable=True)
    estado = Column(String(30), default="AGENDADA", nullable=False)
    notas_medicas = Column(Text, nullable=True)
    creado_en = Column(DateTime, server_default=func.now(), nullable=False)
    actualizado_en = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
