import httpx
from fastapi import HTTPException

# URL del microservicio de doctores
DOCTORES_SERVICE_URL = "https://serviciodoctor.onrender.com"


async def get_recetas_by_paciente_remoto(paciente_id: int):
    """
    Obtiene las recetas de un paciente consumiendo el microservicio
    de doctores mediante HTTP.
    """

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{DOCTORES_SERVICE_URL}/doctor/recetas-paciente",
                params={
                    "paciente_id": paciente_id,
                    "doctor_id": 1   # ID temporal mientras el endpoint lo requiera
                }
            )

            # Lanza excepción si devuelve 4xx o 5xx
            response.raise_for_status()

            # Devuelve las recetas en formato JSON
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Error del microservicio de doctores: {e.response.text}"
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse con el microservicio de doctores."
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado: {str(e)}"
            )
