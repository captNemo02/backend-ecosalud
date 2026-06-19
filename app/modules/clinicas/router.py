from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from datetime import date
from app.database import get_db
from . import schemas, service

router = APIRouter(
    prefix="/clinica",
    tags=["Clínicas & Procedimientos"]
)

@router.post("/procedimiento", response_model=schemas.ProcedimientoResponse, status_code=status.HTTP_201_CREATED)
def crear_procedimiento(procedimiento: schemas.ProcedimientoCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo procedimiento médico, quirúrgico o de diagnóstico en el sistema, 
    asociándolo a un paciente, clínica y opcionalmente a una cita y costo.
    """
    return service.registrar_procedimiento(db=db, procedimiento=procedimiento)

@router.get("/procedimientos", response_model=List[schemas.ProcedimientoResponse])
def listar_procedimientos(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los procedimientos registrados.
    """
    return service.obtener_procedimientos(db=db)

@router.patch("/procedimiento/{id}/costo", response_model=schemas.ProcedimientoResponse)
def actualizar_costo(id: int, costo: Decimal, db: Session = Depends(get_db)):
    """
    Actualiza el costo de un procedimiento específico (usado por el Módulo de Facturación).
    """
    db_procedimiento = service.actualizar_costo_procedimiento(db=db, procedimiento_id=id, costo=costo)
    if not db_procedimiento:
        raise HTTPException(status_code=404, detail="Procedimiento no encontrado")
    return db_procedimiento

@router.get("/sedes", response_model=List[schemas.SedeResponse])
def listar_sedes(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todas las sedes activas de la clínica.
    """
    return service.obtener_sedes(db=db)



@router.get("/citas/{fecha}", response_model=List[schemas.CitaResponse])
def listar_citas_por_fecha(fecha: date, db: Session = Depends(get_db)):
    """
    [MÓDULO CLÍNICA] Obtiene la lista de todas las citas médicas agendadas para una fecha específica (formato YYYY-MM-DD).
    """
    return service.obtener_citas_por_fecha(db=db, fecha_filtro=fecha)
