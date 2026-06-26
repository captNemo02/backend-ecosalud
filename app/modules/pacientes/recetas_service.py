import httpx
from fastapi import HTTPException

DOCTORES_SERVICE_URL = "https://serviciodoctor.onrender.com"


async def get_recetas_by_paciente_remoto(paciente_id: int):
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                f"{DOCTORES_SERVICE_URL}/pacientes/{paciente_id}/recetas"
            )

            if response.status_code == 404:
                return {
                    "paciente_id": paciente_id,
                    "recetas": []
                }

            response.raise_for_status()

            data = response.json()

            return {
                "paciente_id": paciente_id,
                "recetas": data
            }

        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="No se pudo conectar con el microservicio de doctores."
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=502,
                detail="Error al consultar recetas en el microservicio de doctores."
            )
