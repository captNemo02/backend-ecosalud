# app/modules/pacientes/estadisticas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
import httpx
from datetime import datetime

# Importamos los modelos de tus esquemas correspondientes
from app.modules.pacientes.models import Receta, Paciente

async def obtener_metricas_personales_paciente(db: Session, paciente_id: int):
    try:
        # Verificar que el paciente exista en el sistema
        paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        # --- OBTENER CITAS DE LA API EXTERNA ---
        citas_paciente = []
        async with httpx.AsyncClient() as client:
            try:
                # Consultar el listado de citas remoto filtrando por paciente_id
                url = "https://api-clinica-soa.onrender.com/clinica/citas"
                response = await client.get(url, params={"paciente_id": paciente_id})
                if response.status_code == 200:
                    citas_paciente = response.json()
            except Exception as e:
                # Si falla, simplemente dejamos citas_paciente como lista vacía para no romper el dashboard
                print(f"Error al obtener citas remotas para estadísticas: {e}")

        # --- GRÁFICO 1: ESTADO DE MIS CITAS MÉDICAS (Pie Chart / Torta) ---
        # Cuenta tus citas agrupadas por estado: AGENDADA, CONFIRMADA, ATENDIDA, CANCELADA, NO_ASISTIO
        counts = {}
        for c in citas_paciente:
            estado = c.get("estado")
            estado_key = estado.upper() if estado else "DESCONOCIDO"
            counts[estado_key] = counts.get(estado_key, 0) + 1

        grafico_citas = [
            {"name": k.capitalize(), "value": v} 
            for k, v in counts.items()
        ]

        # --- GRÁFICO 2: CONTROL DE RECETAS Y MEDICAMENTOS (Bar Chart / Barras) ---
        # Cuenta tus recetas emitidas según su estado actual: VIGENTE, ENTREGADO, CADUCADO
        recetas_paciente = []

async with httpx.AsyncClient(timeout=15.0) as client:
    try:
        url_recetas = f"https://serviciodoctor.onrender.com/pacientes/{paciente_id}/recetas"
        response_recetas = await client.get(url_recetas)

        if response_recetas.status_code == 200:
            recetas_paciente = response_recetas.json()
    except Exception as e:
        print(f"Error al obtener recetas remotas para estadísticas: {e}")

counts_recetas = {}

for r in recetas_paciente:
    estado = r.get("estado")
    estado_key = estado.upper() if estado else "SIN ESTADO"
    counts_recetas[estado_key] = counts_recetas.get(estado_key, 0) + 1

grafico_recetas = [
    {"estado": k, "cantidad": v}
    for k, v in counts_recetas.items()
]

        # --- GRÁFICO 3: EVOLUCIÓN MENSUAL DE MIS VISITAS (Line Chart / Líneas) ---
        # Agrupa cronológicamente todas tus citas por mes para evaluar tu tendencia de salud
        tendencia = {}
        for c in citas_paciente:
            fecha_str = c.get("fecha_hora")
            if not fecha_str:
                continue
            try:
                dt = datetime.fromisoformat(fecha_str.split(".")[0])
                key = (dt.year, dt.month)
                tendencia[key] = tendencia.get(key, 0) + 1
            except Exception:
                continue

        sorted_keys = sorted(tendencia.keys())
        NOMBRES_MESES = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        grafico_tendencia = [
            {"periodo": f"{NOMBRES_MESES.get(mes, 'Mes')} {year}", "visitas": tendencia[(year, mes)]}
            for year, mes in sorted_keys
        ]

        # --- RETORNO DE DATOS CONSOLIDADOS PARA EL FRONTEND ---
        return {
            "paciente_nombre": f"{paciente.nombres} {paciente.apellidos}",
            "grafico_citas": grafico_citas,
            "grafico_recetas": grafico_recetas,
            "grafico_tendencia": grafico_tendencia
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el procesamiento analítico de datos: {str(e)}"
        )
