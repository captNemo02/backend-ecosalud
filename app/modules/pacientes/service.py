from datetime import datetime, date
import httpx
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
    if paciente.fecha_nacimiento > date.today():
        raise HTTPException(
            status_code=400, 
            detail="La fecha de nacimiento no puede ser posterior a la fecha actual."
        )

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
    
    if "fecha_nacimiento" in update_data and update_data["fecha_nacimiento"] is not None:
        if update_data["fecha_nacimiento"] > date.today():
            raise HTTPException(
                status_code=400, 
                detail="La fecha de nacimiento no puede ser posterior a la fecha actual."
            )
            
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

# ==========================================
# CONEXIÓN CON MICROSERVICIOS EXTERNOS
# ==========================================

DOCTORES_SERVICE_URL = "https://serviciodoctor.onrender.com"
CLINICA_SERVICE_URL = "https://api-clinica-soa.onrender.com/"

async def get_recetas_by_paciente_remoto(paciente_id: int):
    """
    Se conecta vía HTTP con el microservicio de doctores para obtener 
    las recetas reales emitidas a este paciente.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Construimos la URL apuntando al endpoint exacto de doctores
            url_final = f"{DOCTORES_SERVICE_URL}/doctor/recetas-paciente"
            
            # Hacemos la consulta pasando el paciente_id como parámetro (?paciente_id=X)
            response = await client.get(url_final, params={"paciente_id": paciente_id})
            
            # Si el microservicio de doctores responde con un código de error
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502, 
                    detail="El microservicio de doctores no respondió correctamente o el paciente no tiene recetas."
                )
            
            # Si todo está bien, devolvemos el JSON con las recetas al router
            return response.json()
            
        except httpx.RequestError:
            # En caso de que el servidor de doctores esté caído o lento
            raise HTTPException(
                status_code=503, 
                detail="No se pudo establecer comunicación con el microservicio de doctores (Servicio Temporalmente No Disponible)."
            )
        
async def get_check_recordatorio_cita(paciente_id: int, db: Session = None):
    """
    [POPUP] Consume las citas de clínica, busca la más cercana en el futuro 
    y le avisa a React si debe mostrar el Popup.
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"{CLINICA_SERVICE_URL}/clinica/citas"
            response = await client.get(url, params={"paciente_id": paciente_id})
            
            if response.status_code != 200:
                return {"show_popup": False, "cita": None}
            
            citas_paciente = response.json()
            
            citas_futuras = []
            fecha_hoy = date.today()
            
            for cita in citas_paciente:
                try:
                    fecha_cita = datetime.strptime(cita.get("fecha"), "%Y-%m-%d").date()
                    if fecha_cita >= fecha_hoy:
                        citas_futuras.append((fecha_cita, cita))
                except (ValueError, TypeError):
                    continue
            
            if not citas_futuras:
                return {"show_popup": False, "cita": None}
            
            citas_futuras.sort(key=lambda x: x[0])
            proxima_fecha, proxima_cita = citas_futuras[0]
            
            dias_restantes = (proxima_fecha - fecha_hoy).days
            
            if dias_restantes <= 3:
                return {
                    "show_popup": True,
                    "dias_restantes": dias_restantes,
                    "cita": proxima_cita
                }
            
            return {"show_popup": False, "cita": None}
            
        except httpx.RequestError:
            return {"show_popup": False, "cita": None}
