# app/modules/pacientes/estadisticas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db

# Importamos los modelos de tus esquemas correspondientes
from app.modules.pacientes.models import Receta, Paciente
from app.modules.clinicas.models import Cita 

def obtener_metricas_personales_paciente(db: Session, paciente_id: int):
    try:
        # Verificar que el paciente exista en el sistema
        paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        # --- GRÁFICO 1: ESTADO DE MIS CITAS MÉDICAS (Pie Chart / Torta) ---
        # Cuenta tus citas agrupadas por estado: AGENDADA, CONFIRMADA, ATENDIDA, CANCELADA, NO_ASISTIO
        consulta_citas = (
            db.query(Cita.estado, func.count(Cita.id).label("total"))
            .filter(Cita.paciente_id == paciente_id)
            .group_by(Cita.estado)
            .all()
        )
        grafico_citas = [
            {"name": fila[0].capitalize() if fila[0] else "Desconocido", "value": fila[1]} 
            for fila in consulta_citas
        ]

        # --- GRÁFICO 2: CONTROL DE RECETAS Y MEDICAMENTOS (Bar Chart / Barras) ---
        # Cuenta tus recetas emitidas según su estado actual: VIGENTE, ENTREGADO, CADUCADO
        consulta_recetas = (
            db.query(Receta.estado, func.count(Receta.id).label("total"))
            .filter(Receta.paciente_id == paciente_id)
            .group_by(Receta.estado)
            .all()
        )
        grafico_recetas = [
            {"estado": fila[0].upper() if fila[0] else "SIN ESTADO", "cantidad": fila[1]} 
            for fila in consulta_recetas
        ]

        # --- GRÁFICO 3: EVOLUCIÓN MENSUAL DE MIS VISITAS (Line Chart / Líneas) ---
        # Agrupa cronológicamente todas tus citas por mes para evaluar tu tendencia de salud
        consulta_tendencia = (
          db.query(
                extract('year', Cita.fecha_hora).label('año'),
                extract('month', Cita.fecha_hora).label('mes'),
                func.count(Cita.id).label('total')
            )
            .filter(Cita.paciente_id == paciente_id)
            # Opcional: Filtrar solo el último año para no saturar el gráfico
            # .filter(Cita.fecha_hora >= datetime.now() - timedelta(days=365)) 
            .group_by(extract('year', Cita.fecha_hora), extract('month', Cita.fecha_hora))
            .order_by('año', 'mes')
            .all()
        )
        NOMBRES_MESES = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        grafico_tendencia =  [
            {"periodo": f"{NOMBRES_MESES.get(int(fila[1]), 'Mes')} {int(fila[0])}", "visitas": fila[2]}
            for fila in consulta_tendencia
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
