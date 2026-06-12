# Backend EcoSalud 

Este es el backend del sistema EcoSalud, construido con **FastAPI** y **PostgreSQL**. Esta guía te ayudará a configurar y correr el proyecto en tu computadora local.

---

## 1. Requisitos Previos

Asegúrate de tener instalado en tu computadora:
- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/) (Asegúrate de tener tu servidor de base de datos encendido)

---

## 2. Configuración de Variables de Entorno

Este proyecto usa un archivo `.env` para manejar las configuraciones locales.

1. En la raíz de esta carpeta (`backend-ecosalud`), crea un archivo llamado exactamente `.env`
2. Copia y pega el siguiente contenido, y modifica los valores según la configuración de la base de datos de tu propia computadora:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_contraseña_aqui
DB_NAME=postgres
```
---

## 3. Guía de Instalación y Ejecución

Abre tu terminal dentro de la carpeta `backend-ecosalud` y sigue estos pasos:

### Paso 1: Crear el Entorno Virtual (venv)
Esto creará un espacio aislado para no ensuciar tu computadora con librerías globales.
```bash
python -m venv venv
```

### Paso 2: Activar el Entorno Virtual
Debes activar este entorno **siempre** que vayas a trabajar en el proyecto.
- **En Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\activate
  ```
- **En Linux (Git Bash):**
  ```bash
  source venv/Scripts/activate
  ```

### Paso 3: Instalar Dependencias
Con el entorno activado `(venv)`, instala todas las librerías necesarias:
```bash
pip install -r requirements.txt
```

### Paso 4: Iniciar la Aplicación
Para prender el servidor local (con recarga automática):
```bash
uvicorn app.main:app --reload
```

---

## 4. Probar los Endpoints

Una vez que diga `Application startup complete`, abre tu navegador y entra a:
**[http://localhost:8000/docs](http://localhost:8000/docs)**

Verás la interfaz de Swagger lista para probar la API.

---

### Solución de Problemas
Si por alguna razón mueves la carpeta de lugar o le cambias el nombre, el entorno virtual se corromperá. Para solucionarlo, borra la carpeta `venv` usando:
```powershell
Remove-Item -Recurse -Force venv
```
Y luego repite los pasos del 1 al 4.