# app/modules/pacientes/analiticas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.database import get_db  # Importación exacta según tu árbol de carpetas
from .models import Paciente     # Importación relativa desde el mismo módulo

def obtener_indicadores_direccion_pacientes(db: Session):
    try:
        # --- 1. KPI GLOBAL: RESUMEN DE ESTADOS (Tasa de Activación) ---
        # Cuenta los totales, activos, inactivos y eliminados según tus restricciones CHECK de Postgres
        total = db.query(func.count(Paciente.id)).scalar() or 0
        activos = db.query(func.count(Paciente.id)).filter(Paciente.estado == "ACTIVO").scalar() or 0
        inactivos = db.query(func.count(Paciente.id)).filter(Paciente.estado == "INACTIVO").scalar() or 0
        eliminados = db.query(func.count(Paciente.id)).filter(Paciente.estado == "ELIMINADO").scalar() or 0

        kpis_globales = {
            "total_registrados": total,
            "usuarios_activos": activos,
            "usuarios_inactivos": inactivos,
            "usuarios_eliminados": eliminados
        }

        # --- 2. KPI GRÁFICO 1: DISTRIBUCIÓN POR GÉNERO ---
        # Agrupa dinámicamente según 'MASCULINO', 'FEMENINO' u 'OTRO'
        consulta_genero = (
            db.query(Paciente.genero, func.count(Paciente.id).label("total"))
            .group_by(Paciente.genero)
            .all()
        )
        data_genero = [
            {"criterio": str(fila[0]).capitalize() if fila[0] else "No Especificado", "cantidad": fila[1]} 
            for fila in consulta_genero
        ]

        # --- 3. KPI GRÁFICO 2: SEGMENTACIÓN ANALÍTICA POR RANGOS DE EDAD ---
        # Uso nativo de AGE() y EXTRACT(YEAR...) para PostgreSQL a través de SQLAlchemy
        edad_calculada = func.extract('year', func.age(Paciente.fecha_nacimiento))
        
        # Clasificación por ciclo de vida clínico útil para la toma de decisiones directivas
        segmento_edad_case = case(
            (edad_calculada < 18, 'Menores de Edad (<18)'),
            (edad_calculada.between(18, 30), 'Adulto Joven (18-30)'),
            (edad_calculada.between(31, 60), 'Adulto Contribuyente (31-60)'),
            else_='Adulto Mayor (>60)'
        )

        consulta_edades = (
            db.query(segmento_edad_case.label("rango"), func.count(Paciente.id))
            .group_by("rango")
            .all()
        )
        data_edades = [
            {"rango": fila[0], "cantidad": fila[1]} for fila in consulta_edades
        ]

        # --- RESPUESTA CONSOLIDADA ---
        return {
            "resumen_general": kpis_globales,
            "distribucion_segmento": data_genero,
            "rangos_etarios": data_edades
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error en base de datos al procesar analíticas de dirección: {str(e)}"
        )