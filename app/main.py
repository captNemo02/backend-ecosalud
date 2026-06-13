from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# Importar routers de cada módulo
from app.modules.pacientes.router import router as pacientes_router
from app.modules.clinicas.router import router as clinicas_router

# Importar modelos de SQLAlchemy para registrar sus metadatos
# Esto permite que Base.metadata.create_all detecte las tablas de todos los esquemas
import app.modules.pacientes.models
import app.modules.clinicas.models

# Crear las tablas en la base de datos (si no existen)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ECOSALUD - Plataforma Centralizada de Servicios de Salud",
    description="API Modular (SOA) para conectar Pacientes, Clínicas, Procedimientos y Doctores de ECOSALUD.",
    version="1.0.0"
)

# Configurar middleware de CORS para habilitar la conexión del frontend en React
origins = [
    "https://frontend-ecosalud.onrender.com",
    "https://tu-backend.onrender.com"
]
    allow_origins=["*"],  # Permitir conexiones de cualquier origen en desarrollo
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PATCH, etc.)
    allow_headers=["*"],  # Permitir todas las cabeceras
)

# Incluir routers de módulos de negocio
app.include_router(pacientes_router)
app.include_router(clinicas_router)

