from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from . import schemas, service
from .recetas_service import get_recetas_by_paciente_remoto
from .estadisticas import obtener_metricas_personales_paciente
from .analiticas import obtener_indicadores_direccion_pacientes
from .auth import get_current_paciente_id, create_access_token, create_refresh_token, verify_jwt, create_jwt
from .mfa_service import generate_mfa_code, send_mfa_code

router = APIRouter(
    tags=["Pacientes & Autenticación"]
)

# --- Autenticación ---

@router.post("/paciente/login", response_model=schemas.LoginResponse)
def login_paciente(login_data: schemas.PacienteLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Inicia sesión de un paciente validando su correo y contraseña.
    Genera un código MFA, lo envía al paciente y retorna un token MFA temporal de 5 minutos.
    """
    from .auth import verify_password, hash_password

    paciente = service.get_paciente_by_email(db, email=login_data.email)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifique su correo y contraseña."
        )
    
    # Validar contraseña con retrocompatibilidad (DNI)
    if not paciente.password_hash:
        if login_data.password == paciente.numero_documento:
            # Migrar usuario legacy: hashear DNI y guardar en BD
            paciente.password_hash = hash_password(login_data.password)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas. Verifique su correo y contraseña."
            )
    else:
        if not verify_password(login_data.password, paciente.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas. Verifique su correo y contraseña."
            )
    
    if paciente.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta del paciente está INACTIVA. Póngase en contacto con administración."
        )
        
    # Flujo de MFA
    code = generate_mfa_code()
    paciente.mfa_code = code
    paciente.mfa_code_expires_at = datetime.now() + timedelta(minutes=5)
    db.commit()
    
    # Enviar código MFA (consola/archivo y SMTP si está configurado) en segundo plano para no bloquear
    background_tasks.add_task(send_mfa_code, paciente.email, f"{paciente.nombres} {paciente.apellidos}", code)
    
    # Generar token MFA temporal (5 minutos de validez)
    mfa_token = create_jwt({"sub": str(paciente.id), "type": "mfa"}, 300)
    
    return {
        "mfa_required": True,
        "mfa_token": mfa_token,
        "email": paciente.email
    }

@router.post("/paciente/verify-mfa", response_model=schemas.TokenResponse)
def verify_mfa(verify_data: schemas.MFAVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifica el código de doble factor (MFA) provisto por el paciente.
    Si coincide y está vigente, entrega los tokens de acceso definitivos.
    """
    payload = verify_jwt(verify_data.mfa_token)
    if not payload or payload.get("type") != "mfa":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token MFA inválido o expirado. Inicie sesión nuevamente."
        )
        
    paciente_id = int(payload.get("sub"))
    paciente = service.get_paciente_by_id(db, paciente_id=paciente_id)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado."
        )
        
    # Verificar código y expiración
    if not paciente.mfa_code or paciente.mfa_code != verify_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ingresado es incorrecto."
        )
        
    if not paciente.mfa_code_expires_at or paciente.mfa_code_expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ha expirado. Por favor, solicite uno nuevo."
        )
        
    # Limpiar campos de MFA de la base de datos
    paciente.mfa_code = None
    paciente.mfa_code_expires_at = None
    db.commit()
    
    # Generar access y refresh tokens finales
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

@router.post("/paciente/resend-mfa", response_model=schemas.LoginResponse)
def reenviar_mfa(resend_data: schemas.MFAResendRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Reenvía un nuevo código de MFA utilizando el token de MFA temporal provisto.
    """
    payload = verify_jwt(resend_data.mfa_token)
    if not payload or payload.get("type") != "mfa":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token MFA inválido o expirado. Inicie sesión de nuevo."
        )
        
    paciente_id = int(payload.get("sub"))
    paciente = service.get_paciente_by_id(db, paciente_id=paciente_id)
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado."
        )
        
    if paciente.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva."
        )
        
    # Generar nuevo código MFA
    code = generate_mfa_code()
    paciente.mfa_code = code
    paciente.mfa_code_expires_at = datetime.now() + timedelta(minutes=5)
    db.commit()
    
    # Enviar en segundo plano para no bloquear
    background_tasks.add_task(send_mfa_code, paciente.email, f"{paciente.nombres} {paciente.apellidos}", code)
    
    # Nuevo token MFA temporal
    new_mfa_token = create_jwt({"sub": str(paciente.id), "type": "mfa"}, 300)
    
    return {
        "mfa_required": True,
        "mfa_token": new_mfa_token,
        "email": paciente.email
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

