from sqlalchemy.orm import Session
from sqlalchemy import Date, cast
from datetime import date
from . import models, schemas

def registrar_procedimiento(db: Session, procedimiento: schemas.ProcedimientoCreate):
    db_procedimiento = models.Procedimiento(**procedimiento.model_dump())
    db.add(db_procedimiento)
    db.commit()
    db.refresh(db_procedimiento)
    return db_procedimiento

def obtener_procedimientos(db: Session):
    return db.query(models.Procedimiento).order_by(models.Procedimiento.id.desc()).all()

def actualizar_costo_procedimiento(db: Session, procedimiento_id: int, costo: float):
    db_procedimiento = db.query(models.Procedimiento).filter(models.Procedimiento.id == procedimiento_id).first()
    if db_procedimiento:
        db_procedimiento.costo = costo
        db.commit()
        db.refresh(db_procedimiento)
    return db_procedimiento

def obtener_sedes(db: Session):
    return db.query(models.Sede).filter(models.Sede.activo == True).order_by(models.Sede.id.asc()).all()

def obtener_citas_por_paciente(db: Session, paciente_id: int):
    return db.query(models.Cita).filter(models.Cita.paciente_id == paciente_id).order_by(models.Cita.fecha_hora.desc()).all()

def obtener_todas_citas(db: Session):
    return db.query(models.Cita).order_by(models.Cita.fecha_hora.desc()).all()

def registrar_cita(db: Session, cita: schemas.CitaCreate):
    db_cita = models.Cita(**cita.model_dump())
    db.add(db_cita)
    db.commit()
    db.refresh(db_cita)
    return db_cita

def obtener_citas_por_fecha(db: Session, fecha_filtro: date):
    # Comparar la columna DateTime truncándola a tipo Date
    return db.query(models.Cita).filter(
        cast(models.Cita.fecha_hora, Date) == fecha_filtro
    ).order_by(models.Cita.fecha_hora.asc()).all()
