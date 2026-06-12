from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Paciente


def obtener_resumen(db: Session):
    """
    Obtiene indicadores generales de pacientes.
    """

    total_pacientes = db.query(Paciente).count()

    pacientes_activos = (
        db.query(Paciente)
        .filter(Paciente.estado == "ACTIVO")
        .count()
    )

    pacientes_inactivos = (
        db.query(Paciente)
        .filter(Paciente.estado != "ACTIVO")
        .count()
    )

    return {
        "total_pacientes": total_pacientes,
        "pacientes_activos": pacientes_activos,
        "pacientes_inactivos": pacientes_inactivos
    }


def obtener_genero(db: Session):
    """
    Obtiene la distribución de pacientes por género.
    """

    resultados = (
        db.query(
            Paciente.genero,
            func.count(Paciente.id).label("cantidad")
        )
        .group_by(Paciente.genero)
        .all()
    )

    return [
        {
            "genero": genero if genero else "No especificado",
            "cantidad": cantidad
        }
        for genero, cantidad in resultados
    ]