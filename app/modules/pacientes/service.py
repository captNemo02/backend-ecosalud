from sqlalchemy.orm import Session
from . import models
from . import schemas
from fastapi import HTTPException

def get_paciente_by_numero_documento(db: Session, numero_documento: str):
    return db.query(models.Paciente).filter(models.Paciente.numero_documento == numero_documento).first()

def get_paciente_by_id(db: Session, paciente_id: int):
    return db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()

def get_pacientes(
    db: Session, 
    nombres: str = None, 
    apellidos: str = None, 
    numero_documento: str = None, 
    estado: str = None,
    search: str = None
):
    query = db.query(models.Paciente)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Paciente.nombres.ilike(search_filter)) |
            (models.Paciente.apellidos.ilike(search_filter)) |
            (models.Paciente.numero_documento.ilike(search_filter)) |
            (models.Paciente.email.ilike(search_filter))
        )
    else:
        if nombres:
            query = query.filter(models.Paciente.nombres.ilike(f"%{nombres}%"))
        if apellidos:
            query = query.filter(models.Paciente.apellidos.ilike(f"%{apellidos}%"))
        if numero_documento:
            query = query.filter(models.Paciente.numero_documento == numero_documento)
        if estado:
            query = query.filter(models.Paciente.estado == estado)
            
    return query.order_by(models.Paciente.id.asc()).all()

def create_paciente(db: Session, paciente: schemas.PacienteCreate):
    db_paciente = get_paciente_by_numero_documento(db, numero_documento=paciente.numero_documento)
    if db_paciente:
        raise HTTPException(status_code=400, detail="El paciente con este número de documento ya está registrado")
    
    db_paciente = models.Paciente(**paciente.model_dump())
    db.add(db_paciente)
    db.commit()
    db.refresh(db_paciente)
    return db_paciente

def update_paciente(db: Session, paciente_id: int, paciente_update: schemas.PacienteUpdate):
    db_paciente = get_paciente_by_id(db, paciente_id)
    if not db_paciente:
        return None
    
    # Extraer solo los datos que el usuario envió (que no son nulos)
    update_data = paciente_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_paciente, key, value)
        
    db.commit()
    db.refresh(db_paciente)
    return db_paciente

def get_historial_clinico_by_paciente(db: Session, paciente_id: int):
    # Verificar si el paciente existe
    paciente = get_paciente_by_id(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
    return db.query(models.HistorialClinico).filter(models.HistorialClinico.paciente_id == paciente_id).all()

def get_recetas_by_paciente(db: Session, paciente_id: int):
    # Verificar si el paciente existe
    paciente = get_paciente_by_id(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
    return db.query(models.Receta).filter(models.Receta.paciente_id == paciente_id).all()


def get_paciente_by_email_and_documento(db: Session, email: str, numero_documento: str):
    return db.query(models.Paciente).filter(
        models.Paciente.email == email,
        models.Paciente.numero_documento == numero_documento
    ).first()


def create_orden_medica(db: Session, orden: schemas.OrdenMedicaCreate):
    # Verificar si el paciente existe
    paciente = get_paciente_by_id(db, orden.paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
    db_orden = models.OrdenMedica(**orden.model_dump())
    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    return db_orden


def get_ordenes_medicas_by_paciente(db: Session, paciente_id: int):
    # Verificar si el paciente existe
    paciente = get_paciente_by_id(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
    return db.query(models.OrdenMedica).filter(models.OrdenMedica.paciente_id == paciente_id).order_by(models.OrdenMedica.id.desc()).all()

