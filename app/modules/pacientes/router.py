from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from . import schemas, service
from .recetas_service import get_recetas_by_paciente_remoto
from .estadisticas import obtener_metricas_personales_paciente
from .analiticas import obtener_indicadores_direccion_pacientes
from .auth import get_current_paciente_id, create_access_token, create_refresh_token, verify_jwt

router = APIRouter(
    tags=["Pacientes & Autenticación"]
)

# --- Autenticación ---

@router.post("/paciente/login", response_model=schemas.TokenResponse)
def login_paciente(login_data: schemas.PacienteLogin, db: Session = Depends(get_db)):
    """
    Inicia sesión de un paciente validando su correo y su número de documento (DNI).
    Genera un access token (válido por 15 minutos) y un refresh token (válido por 24 horas).
    """
    paciente = service.get_paciente_by_email_and_documento(
        db, email=login_data.email, numero_documento=login_data.numero_documento
    )
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifique su correo y DNI."
        )
    
    if paciente.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta del paciente está INACTIVA. Póngase en contacto con administración."
        )
        
    access_token = create_access_token(paciente.id)
    refresh_token = create_refresh_token(paciente.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "paciente_id": paciente.id,
        "nombres": paciente.nombres,
        "apellidos": paciente.apellidos
    }

@router.post("/paciente/refresh")
def refrescar_token(refresh_data: schemas.TokenRefreshRequest):
    """
    Renueva el access token del paciente utilizando su refresh token vigente.
    Si el refresh token es válido, retorna un nuevo access token.
    """
    payload = verify_jwt(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado. Inicie sesión nuevamente."
        )
        
    paciente_id = int(payload.get("sub"))
    new_access_token = create_access_token(paciente_id)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

# --- Registro de Paciente (Público) ---

@router.post("/paciente/registro", response_model=schemas.PacienteResponse)
def crear_paciente(paciente: schemas.PacienteCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo paciente en el sistema (portal web o app móvil).
    """
    return service.create_paciente(db=db, paciente=paciente)

# --- Endpoints Protegidos del Paciente ---

@router.get("/pacientes", response_model=List[schemas.PacienteResponse])
def obtener_pacientes(
    numero_documento: str = None,
    nombres: str = None,
    apellidos: str = None,
    estado: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de pacientes registrados con filtros opcionales (nombre, apellido, dni, estado, o búsqueda general).
    """
    return service.get_pacientes(
        db=db,
        nombres=nombres,
        apellidos=apellidos,
        numero_documento=numero_documento,
        estado=estado,
        search=search
    )

@router.get("/paciente/{id}", response_model=schemas.PacienteResponse)
def obtener_paciente(id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un paciente específico por su ID.
    """
    # [COMENTADO POR SEGURIDAD / ACCESO PÚBLICO]
    # if current_paciente_id != id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Acceso denegado. No está autorizado para ver este perfil."
    #     )
        
    paciente = service.get_paciente_by_id(db, paciente_id=id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@router.patch("/paciente/{id}", response_model=schemas.PacienteResponse)
def actualizar_paciente(id: int, paciente_update: schemas.PacienteUpdate, db: Session = Depends(get_db)):
    """
    Actualiza parcialmente los datos de un paciente.
    """
    # [COMENTADO POR SEGURIDAD / ACCESO PÚBLICO]
    # if paciente_update.estado is None and current_paciente_id != id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Acceso denegado. No está autorizado para modificar este perfil."
    #     )
        
    paciente_db = service.update_paciente(db, paciente_id=id, paciente_update=paciente_update)
    if not paciente_db:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente_db

@router.get("/paciente/{id}/historial-clinico", response_model=List[schemas.HistorialClinicoResponse])
def obtener_historial_clinico(id: int, db: Session = Depends(get_db)):
    """
    Obtiene todo el historial clínico asociado a un paciente específico.
    """
    # [COMENTADO POR SEGURIDAD / ACCESO PÚBLICO]
    # if current_paciente_id != id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Acceso denegado. No está autorizado para ver este historial clínico."
    #     )
    return service.get_historial_clinico_by_paciente(db=db, paciente_id=id)

@router.get("/paciente/{id}/recetas-remotas")
async def obtener_recetas_remotas(id: int):
    """
    [MICROSERVICIOS] Obtiene las recetas médicas reales del paciente 
    consumiendo en tiempo real el Microservicio de Doctores en Render.
    """
    return await get_recetas_by_paciente_remoto(paciente_id=id)
    

@router.get("/paciente/{id}/ordenes-medicas", response_model=List[schemas.OrdenMedicaResponse])
def obtener_ordenes_medicas(id: int, db: Session = Depends(get_db)):
    """
    Obtiene todas las órdenes médicas (exámenes de laboratorio, imagenología) del paciente.
    """
    # [COMENTADO POR SEGURIDAD / ACCESO PÚBLICO]
    # if current_paciente_id != id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Acceso denegado. No está autorizado para ver estas órdenes médicas."
    #     )
    return service.get_ordenes_medicas_by_paciente(db=db, paciente_id=id)


# --- Endpoint Simulado del Doctor (Emisión de Órdenes) ---

@router.post("/doctor/orden-medica", response_model=schemas.OrdenMedicaResponse, status_code=status.HTTP_201_CREATED)
def crear_orden_medica(orden: schemas.OrdenMedicaCreate, db: Session = Depends(get_db)):
    """
    [MÓDULO DOCTOR] Registra una orden médica para un paciente (análisis, rayos X, interconsulta, etc.).
    Simula el servicio del módulo Doctor consumido por el Portal del Paciente.
    """
    return service.create_orden_medica(db=db, orden=orden)

@router.get("/pacientes/estadisticas/resumen")
def estadisticas_resumen(
    db: Session = Depends(get_db)
):
    """
    Devuelve indicadores generales de pacientes.
    """
    return obtener_indicadores_direccion_pacientes(db)

@router.get("/clinica/direccion/gestion-pacientes")
def estadisticas_direccion_pacientes(
    db: Session = Depends(get_db)
):
    """
    [PANEL DE DIRECCIÓN] Devuelve indicadores estratégicos unificados de pacientes:
    Resumen global de estados (activos/inactivos), distribución por género y rangos de edad.
    """
    return obtener_indicadores_direccion_pacientes(db)
@router.get("/dashboard/metricas-personales/{paciente_id}")
async def get_metricas_paciente(paciente_id: int, db: Session = Depends(get_db)):
    """
    Retorna los 3 gráficos clave de control personal para el portal del paciente:
    Citas médicas, balance de recetas y tendencia mensual de visitas.
    """
    return await obtener_metricas_personales_paciente(db, paciente_id=paciente_id)

@router.get("/paciente/{id}/check-recordatorio")
async def verificar_recordatorio_cita(id: int, db: Session = Depends(get_db)):
    """
    [POPUP] Endpoint para que React consulte si el paciente tiene una cita pronta
    a menos de 3 días en el microservicio clínico de la otra sección.
    """
    # Llama a la lógica de negocio que evalúa las fechas de las citas
    return await service.get_check_recordatorio_cita(db=db, paciente_id=id)

