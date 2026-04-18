# Document Intelligence API

El objetivo de este proyecto es construir una API RESTful escalable y robusta que permita a los usuarios subir documentos, extraer información mediante Inteligencia Artificial y procesar estas tareas en segundo plano. Este proyecto está diseñado para demostrar habilidades avanzadas de Backend (FastAPI, procesamiento asíncrono, bases de datos) e integración con IA.

## User Review Required

> [!IMPORTANT]
> Por favor, revisa la estructura propuesta y las tecnologías a utilizar. Una vez que apruebes este plan, comenzaré a generar la estructura de carpetas y los archivos base.

## Open Questions

> [!WARNING]
> Tengo un par de preguntas antes de empezar a codificar para adaptar el proyecto a tus preferencias:
> 1. **Proveedor de IA:** ¿Quieres usar la API de OpenAI (ChatGPT - requiere tarjeta/pago por uso), o prefieres que usemos una alternativa gratuita como Groq (modelos Llama 3 ultrarrápidos y gratis) para que no tengas que gastar dinero mientras desarrollas? prefiero el mejor modelo gratis existente, que no ocupe demaciado mi laptop he visto que ollama es bueno pero nose  cual sea el mejor, cual me recomiendas?   
> 2. **Gestor de paquetes:** ¿Prefieres el clásico `requirements.txt` y `venv` o te gustaría usar una herramienta más moderna que gusta mucho en las empresas como `uv` o `Poetry`? Si no estás seguro, recomiendo `uv` por su velocidad.
uv esta bien    
## Proposed Changes

El proyecto se creará en el directorio `C:\Users\alexa\.gemini\antigravity\scratch\document_intelligence_api`. Se recomienda que abras esta carpeta en tu editor de código (como VS Code) como tu espacio de trabajo (workspace).

La arquitectura seguirá las mejores prácticas para FastAPI, separando responsabilidades (Clean Architecture):

### Estructura Base y Configuración
Generaremos los cimientos del proyecto, incluyendo Docker y dependencias.

#### [NEW] `docker-compose.yml`
Para levantar la base de datos PostgreSQL y Redis de forma local sin tener que instalar nada en tu PC.

#### [NEW] `Dockerfile`
Para empaquetar la aplicación.

#### [NEW] `requirements.txt` o `pyproject.toml`
Dependiendo de tu respuesta a las preguntas abiertas, configuraremos las dependencias (FastAPI, Uvicorn, SQLAlchemy, Celery, Redis, Pydantic, etc).

#### [NEW] `app/main.py`
El punto de entrada de la aplicación FastAPI.

### Módulo de Configuración y Base de Datos
#### [NEW] `app/core/config.py`
Para gestionar las variables de entorno (claves de API, credenciales de base de datos) usando Pydantic Settings.

#### [NEW] `app/core/database.py`
Configuración de la conexión a PostgreSQL usando SQLAlchemy asíncrono.

### Modelos y Esquemas
#### [NEW] `app/models/user.py` y `app/models/document.py`
Modelos de base de datos SQLAlchemy para almacenar los usuarios y el estado/metadatos de los documentos.

#### [NEW] `app/schemas/user.py` y `app/schemas/document.py`
Modelos Pydantic para validar los datos que entran y salen de la API.

### Rutas (Endpoints) y Lógica de Negocio
#### [NEW] `app/api/auth.py`
Rutas para registrarse e iniciar sesión (JWT).

#### [NEW] `app/api/documents.py`
Rutas para subir PDFs/Textos y consultar su estado de análisis.

#### [NEW] `app/services/ai_service.py`
Lógica de integración con la IA (OpenAI o Groq) para extraer texto y generar resúmenes.

### Tareas en Segundo Plano (Background Workers)
#### [NEW] `app/worker/celery_app.py`
Configuración de Celery para conectarse a Redis.

#### [NEW] `app/worker/tasks.py`
Las tareas que se ejecutarán en segundo plano (ej. `process_document_task`) para no bloquear la API mientras la IA responde.

## Verification Plan

### Automated Tests
- Crearemos la carpeta `tests/` y configuraremos `pytest`.
- Escribiremos pruebas para verificar que el registro de usuario funciona.
- Escribiremos pruebas para asegurar que el endpoint de subida de archivos acepta los formatos correctos.

### Manual Verification
- Levantaremos los servicios con `docker-compose up -d`.
- Iniciaremos el servidor local `uvicorn app.main:app --reload`.
- Visitaremos `http://localhost:8000/docs` para ver la interfaz interactiva de Swagger, donde probaremos subir un archivo y veremos cómo una tarea de Celery lo procesa.
