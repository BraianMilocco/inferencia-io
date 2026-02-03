# 🎬 Video Analysis API - Django + LangGraph

API REST para análisis de videos de YouTube o archivos MP4 mediante un flujo de agentes orquestado con **LangGraph**. El sistema extrae la transcripción, analiza el sentimiento y tono, y genera un resumen estructurado con los 3 puntos clave del contenido.

## 📋 Tabla de Contenidos

- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Instalación y Setup](#-instalación-y-setup)
- [Variables de Entorno](#-variables-de-entorno)
- [API Endpoints](#-api-endpoints)
- [Modelo de Datos](#-modelo-de-datos)
- [Arquitectura LangGraph](#-arquitectura-langgraph)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Decisiones de Diseño](#-decisiones-de-diseño)

---

## 🛠 Stack Tecnológico

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.12+ | Runtime |
| Django | 6.0.1 | Framework web |
| Django REST Framework | 3.16.1 | API REST |
| LangGraph | 1.0.7 | Orquestación de agentes |
| LangChain | 1.2.8 | Framework LLM |
| OpenAI Whisper | API | Transcripción de audio |
| OpenAI GPT | gpt-4o-mini | Análisis de sentimiento y estructuración |
| PostgreSQL | 16 | Base de datos |
| yt-dlp | 2026.1.31 | Descarga de audio de YouTube |
| FFmpeg | - | Procesamiento de audio |
| Docker | - | Containerización |
| uv | - | Gestor de paquetes Python |

---

## 🏗 Arquitectura del Sistema

```
┌─────────────────┐     ┌─────────────────────────────────────────────────┐
│   Cliente       │     │                   Django REST API               │
│  (POST video)   │────▶│  /api/analyze/youtube/  │  /api/analyze/mp4/   │
└─────────────────┘     └─────────────────────────────────────────────────┘
                                           │
                                           ▼
                        ┌─────────────────────────────────────────────────┐
                        │              LangGraph Workflow                  │
                        │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
                        │  │Extraction│─▶│Sentiment │─▶│ Structuring  │   │
                        │  │   Node   │  │  Node    │  │    Node      │   │
                        │  └──────────┘  └──────────┘  └──────────────┘   │
                        └─────────────────────────────────────────────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
                   ┌─────────┐      ┌───────────┐      ┌───────────┐
                   │ Whisper │      │  OpenAI   │      │PostgreSQL │
                   │   API   │      │    GPT    │      │    DB     │
                   └─────────┘      └───────────┘      └───────────┘
```

---

## 🚀 Instalación y Setup

### Prerrequisitos

- Docker y Docker Compose
- (Opcional para desarrollo local) Python 3.12+, uv, FFmpeg

### Opción 1: Docker Compose Completo (Recomendado)

Levanta la aplicación completa (API + PostgreSQL):

```bash
# 1. Clonar el repositorio
git clone git@github.com:BraianMilocco/inferencia-io.git
cd challenge

# 2. Crear archivo .env (ver sección Variables de Entorno)
cp .env.example .env
# Editar .env con tus credenciales

# 3. Levantar servicios
docker compose up --build

# La API estará disponible en http://localhost:8000
```

### Opción 2: Solo Base de Datos (Desarrollo Local)

Útil para desarrollo local con hot-reload:

```bash
# 1. Levantar solo PostgreSQL
docker compose -f docker-compose.dev.yml up -d

# 2. Instalar dependencias localmente
uv sync

# 3. Configurar .env con DB_HOST=localhost
# DB_HOST=localhost

# 4. Ejecutar migraciones
uv run python manage.py migrate

# 5. Iniciar servidor de desarrollo
uv run python manage.py runserver
```

### Opción 3: Setup Completamente Local

```bash
# 1. Instalar PostgreSQL localmente
# (instrucciones varían según SO)

# 2. Instalar FFmpeg
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS

# 3. Instalar dependencias
uv sync

# 4. Configurar .env (ver sección Variables de Entorno)

# 5. Ejecutar migraciones
uv run python manage.py migrate

# 6. Iniciar servidor
uv run python manage.py runserver
```

---

## 🔐 Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# ═══════════════════════════════════════════════════════════
# PostgreSQL
# ═══════════════════════════════════════════════════════════
POSTGRES_DB=video_analysis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db                    # Usar 'db' para Docker, 'localhost' para local
DB_PORT=5432

# ═══════════════════════════════════════════════════════════
# Django
# ═══════════════════════════════════════════════════════════
DEBUG=True                    # False en producción
ALLOWED_HOSTS=*               # Restringir en producción

# ═══════════════════════════════════════════════════════════
# OpenAI (REQUERIDO)
# ═══════════════════════════════════════════════════════════
LLM_API_KEY=sk-proj-xxx...    # Tu API key de OpenAI

# ═══════════════════════════════════════════════════════════
# Opcionales
# ═══════════════════════════════════════════════════════════
LLM_MODEL_NAME=gpt-4o-mini    # Modelo para análisis (default: gpt-4o-mini)
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR
```

> ⚠️ **Importante**: `LLM_API_KEY` es obligatorio. Se usa tanto para Whisper (transcripción) como para GPT (análisis).

---

## 📡 API Endpoints

### Base URL: `http://localhost:8000/api/`

### 1. Análisis de Video de YouTube

#### `POST /api/analyze/youtube/`

Analiza un video de YouTube a partir de su URL.

**Request Body** (JSON):
```json
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response** (201 Created):
```json
{
  "video_metadata": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration_seconds": 213,
    "language_code": "en"
  },
  "analysis": {
    "sentiment": "positive",
    "sentiment_score": 0.85,
    "tone": "motivational",
    "key_points": [
      "El cantante expresa un compromiso inquebrantable hacia su pareja",
      "La canción enfatiza la lealtad y la confianza en las relaciones",
      "El mensaje central es sobre nunca abandonar a alguien que amas"
    ]
  }
}
```

#### `GET /api/analyze/youtube/`

Lista los análisis previos de videos de YouTube (paginado).

**Query Parameters**:
- `page`: Número de página (default: 1)

**Response** (200 OK):
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/analyze/youtube/?page=2",
  "previous": null,
  "results": [
    {
      "video_metadata": { ... },
      "analysis": { ... }
    }
  ]
}
```

---

### 2. Análisis de Video MP4

#### `POST /api/analyze/mp4/`

Analiza un archivo de video MP4 subido.

**Request**: `multipart/form-data`
- Campo `video`: Archivo MP4

**Response** (201 Created):
```json
{
  "video_metadata": {
    "title": "mi video de ejemplo",
    "duration_seconds": 120,
    "language_code": "es"
  },
  "analysis": {
    "sentiment": "neutral",
    "sentiment_score": 0.52,
    "tone": "informativo",
    "key_points": [
      "Punto clave 1 del video",
      "Punto clave 2 del video",
      "Punto clave 3 del video"
    ]
  }
}
```

#### `GET /api/analyze/mp4/`

Lista los análisis previos de videos subidos (paginado).

---

### Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Listado exitoso |
| 201 | Análisis creado exitosamente |
| 400 | Error de validación (URL inválida, archivo no MP4) |
| 500 | Error interno durante el análisis |

**Ejemplo de error por audio insuficiente** (500):
```json
{
  "error": "Error during analysis",
  "details": ["Audio not found or insufficient. Transcript too short: 1 words, 3 characters. Minimum required: 5 words or 10 characters."]
}
```

---

## 🗃 Modelo de Datos

### VideoAnalysis

```python
class VideoAnalysis(models.Model):
    # Identificación
    video_url          # URLField - URL del video o "upload://filename.mp4"
    created_at         # DateTimeField - Fecha de creación
    updated_at         # DateTimeField - Última actualización
    
    # Metadata del video
    title              # CharField(500) - Título del video
    duration_seconds   # IntegerField - Duración en segundos
    language_code      # CharField(10) - Código ISO 639-1 (ej: "en", "es")
    
    # Transcripción
    transcript         # TextField - Texto completo transcrito
    
    # Análisis
    sentiment          # CharField - "positive", "negative", "neutral"
    sentiment_score    # FloatField - Score 0.0 a 1.0
    tone               # CharField(100) - Tono detectado
    key_points         # ArrayField[TextField, size=3] - 3 puntos clave
    
    # Errores
    errors             # ArrayField[TextField] - Lista de errores (si hubo)
```

> 📝 Se utiliza `ArrayField` de PostgreSQL para `key_points` y `errors` ya que permite almacenar listas de forma nativa y eficiente.

---

## 🔄 Arquitectura LangGraph

### Diagrama del Grafo

```
                    ┌─────────────────┐
                    │      START      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   EXTRACTION    │
                    │      NODE       │
                    │                 │
                    │ • Descarga audio│
                    │ • Whisper API   │
                    │ • Metadata      │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │ should_continue │ ──── errors? ────▶ END
                    └────────┬────────┘
                             │ continue
                             ▼
                    ┌─────────────────┐
                    │    SENTIMENT    │
                    │  ANALYSIS NODE  │
                    │                 │
                    │ • Sentiment     │
                    │ • Score         │
                    │ • Tone          │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │ should_continue │ ──── errors? ────▶ END
                    └────────┬────────┘
                             │ continue
                             ▼
                    ┌─────────────────┐
                    │   STRUCTURING   │
                    │      NODE       │
                    │                 │
                    │ • 3 Key Points  │
                    │ • Final JSON    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │       END       │
                    └─────────────────┘
```

### Estado Compartido (VideoAnalysisState)

```python
class VideoAnalysisState(TypedDict):
    # Input
    video_url: Optional[str]          # URL de YouTube o "upload://..."
    video_path: Optional[str]         # Path local (solo para uploads)
    
    # Extraction outputs
    transcript: Optional[str]
    title: Optional[str]
    duration_seconds: Optional[int]
    language_code: Optional[str]
    
    # Sentiment analysis outputs
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    tone: Optional[str]
    
    # Structuring outputs
    key_points: Optional[List[str]]
    final_result: Optional[dict]
    
    # Control de flujo
    errors: Optional[List[str]]
    status: Optional[str]             # "processing", "extracted", "analyzed", "success", "failed", "skipped"
```

### Nodos del Grafo

#### Nodo 1: Extraction
- **Entrada**: `video_url` o `video_path`
- **Proceso**:
  - Para YouTube: Descarga audio con `yt-dlp`, extrae metadata
  - Para uploads: Extrae audio con `FFmpeg`, obtiene duración con `ffprobe`
  - Transcribe con OpenAI Whisper API
  - **Validación de transcripción**: Verifica que el transcript tenga al menos 5 palabras o 10 caracteres
- **Salida**: `transcript`, `title`, `duration_seconds`, `language_code`
- **Error si**: El transcript es demasiado corto (indica video sin audio o audio insuficiente)

#### Nodo 2: Sentiment Analysis
- **Entrada**: `transcript`
- **Proceso**: Analiza con GPT usando prompt especializado y Pydantic parser
- **Salida**: `sentiment`, `sentiment_score`, `tone`

#### Nodo 3: Structuring
- **Entrada**: `transcript` + outputs de nodos anteriores
- **Proceso**: Extrae 3 puntos clave con GPT y estructura el JSON final
- **Salida**: `key_points`, `final_result`

### Edges Condicionales

El grafo implementa edges condicionales para manejar errores:

```python
def should_continue(state: VideoAnalysisState) -> str:
    if state.get("errors") or state.get("status") in ["failed", "skipped"]:
        return "end"
    return "continue"
```

Esto permite que si un nodo falla, el flujo termine prematuramente sin ejecutar nodos innecesarios.

---

## 📁 Estructura del Proyecto

```
challenge/
├── docker-compose.yml          # Docker Compose (app + db)
├── docker-compose.dev.yml      # Docker Compose (solo db)
├── Dockerfile                  # Imagen de la aplicación
├── pyproject.toml              # Dependencias y configuración
├── manage.py                   # Django CLI
├── helpers.py                  # Funciones helper globales
│
├── challenge_inferencia/       # Configuración Django
│   ├── settings.py             # Settings (DB, REST Framework, etc.)
│   ├── urls.py                 # URLs raíz
│   └── wsgi.py / asgi.py       # Entry points
│
└── graph/                      # App principal
    ├── models.py               # Modelo VideoAnalysis
    ├── views.py                # Vistas API (YouTube, MP4)
    ├── urls.py                 # Rutas /api/analyze/*
    ├── serializers.py          # Serializers DRF
    ├── admin.py                # Admin Django
    │
    └── agents/                 # Lógica LangGraph
        ├── graph.py            # Definición del grafo
        ├── state.py            # VideoAnalysisState
        ├── nodes.py            # Implementación de nodos
        ├── prompts.py          # Prompts para LLM
        ├── llm_config.py       # Configuración OpenAI
        │
        └── services/
            └── whisper.py      # Servicio de transcripción
```

---

## 🎯 Decisiones de Diseño

### ¿Por qué LangGraph?

1. **Flujo visual y declarativo**: La definición del grafo hace explícito el flujo de datos
2. **Estado tipado**: `TypedDict` garantiza consistencia en el estado compartido
3. **Edges condicionales**: Permiten manejo elegante de errores sin try/catch anidados
4. **Extensibilidad**: Agregar nuevos nodos (ej: detección de temas, resumen ejecutivo) es trivial
5. **Debugging**: El estado es inspeccionable en cada paso

### ¿Por qué PostgreSQL con ArrayField?

- `key_points` siempre son exactamente 3 elementos
- `errors` es una lista variable de strings
- `ArrayField` es más eficiente que una tabla separada para relaciones 1:N simples
- Permite queries directos: `VideoAnalysis.objects.filter(key_points__contains=["palabra"])`

### Manejo de Errores

1. **Persistencia de errores**: Los errores se guardan en la DB para debugging posterior
2. **Fail-fast con edges condicionales**: Si un nodo falla, no se ejecutan los siguientes
3. **Cleanup de archivos temporales**: El audio temporal se elimina siempre (incluso en error)
4. **Validación temprana**: Los serializers validan URL/archivo antes de procesar
5. **Validación de audio insuficiente**: Si la transcripción es muy corta (< 5 palabras o < 10 caracteres), se retorna error `"Audio not found or insufficient"`. Esto previene que Whisper "alucine" texto en videos sin audio real

### Separación de Concerns

```
views.py          → HTTP request/response
serializers.py    → Validación y formato de datos
graph.py          → Orquestación del flujo
nodes.py          → Lógica de negocio por nodo
services/         → Integraciones externas (Whisper)
prompts.py        → Prompt engineering (separado para fácil iteración)
```

### Paginación

Se utiliza la paginación nativa de Django REST Framework configurada globalmente en `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
```

Esto permite paginar cualquier endpoint GET automáticamente sin código adicional en las vistas.

---

## 🧪 Verificar Instalación

```bash
# Verificar que los servicios están corriendo
docker compose ps

# Ver logs
docker compose logs -f web

# Probar endpoint de health (Django admin)
curl http://localhost:8000/admin/

# Ejecutar una prueba rápida
curl -X POST http://localhost:8000/api/analyze/youtube/ \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
```

---

## 📊 Logs y Debugging

El nivel de log se configura con `LOG_LEVEL` en `.env`:

```bash
# Ver logs detallados
LOG_LEVEL=DEBUG docker compose up
```

Logs importantes:
- `graph.agents.graph`: Flujo del grafo
- `graph.agents.nodes`: Ejecución de nodos
- `graph.agents.services.whisper`: Transcripción

---

## 🧪 Testing

El proyecto incluye tests para validar el endpoint de análisis de videos de YouTube.

### Ejecutar Tests

**Con Docker:**
```bash
docker compose exec web uv run python manage.py test graph.tests
```

**Localmente:**
```bash
uv run python manage.py test graph.tests
```

**Con coverage:**
```bash
# Instalar coverage
uv add coverage

# Ejecutar tests con coverage
uv run coverage run --source='.' manage.py test graph.tests
uv run coverage report
uv run coverage html  # Genera reporte HTML en htmlcov/
```

### Casos de Prueba

Los tests cubren los siguientes escenarios para la vista `VideoAnalysisYoutubeView`:

| Escenario | URL de prueba | Resultado esperado |
|-----------|---------------|-------------------|
| ✅ Video con audio | `youtube.com/watch?v=ssYt09bCgUY` | 201 Created |
| ⚠️ Video sin audio | `youtube.com/watch?v=6TBKF6GF9-g` | 500 Error (audio insuficiente) |
| ❌ Video inexistente | `youtube.com/watch?v=AAASADADADADADADADDA` | 500 Error |
| ❌ URL inválida | `yoyobe.com/watch?v=6TBKF6GF9-g` | 400/500 Error |
| ✅ Paginación | GET con `?page=2` | 200 OK |

### Tests Pendientes

Los siguientes tests no están implementados pero podrían agregarse en el futuro:

- ❌ **Tests para `VideoAnalysisUploadView`**: No implementados para evitar la necesidad de descargar y almacenar archivos de video de prueba en el repositorio. El endpoint `/api/analyze/mp4/` ha sido probado manualmente y funciona correctamente.
- ❌ **Tests unitarios del grafo de LangGraph**: Tests específicos para cada nodo (`extraction_node`, `sentiment_analysis_node`, `structuring_node`) y las funciones condicionales.
- ❌ **Tests de flujo completo del grafo**: Validación del flujo end-to-end con diferentes estados y transiciones.

### Tests de Integración

⚠️ **ADVERTENCIA**: El test `test_full_flow_with_real_video` hace llamadas reales a:
- YouTube (yt-dlp)
- OpenAI API (Whisper + GPT)

**Esto consume créditos de API y puede ser lento.** Para ejecutar solo tests unitarios sin integración:

```bash
uv run python manage.py test graph.tests.VideoAnalysisYoutubeAPITestCase --exclude-tag=integration
uv run python manage.py test graph.tests.VideoAnalysisModelTestCase
```

---

## 🚧 Mejoras Futuras

Este proyecto fue desarrollado como prueba técnica y cumple con todos los requisitos solicitados. Sin embargo, existen mejoras que podrían implementarse en un entorno de producción:

### 🔄 Persistencia de Estado de Agentes

**Estado actual**: El sistema procesa cada video de forma independiente sin mantener contexto entre ejecuciones.

**Mejora propuesta**: 
- Implementar **LangGraph Checkpointing** para persistir el estado del grafo y permitir reanudar ejecuciones interrumpidas
- Alternativa: Usar **Redis** como backend de persistencia para estados intermedios
- Beneficio: Recuperación ante fallos, debugging mejorado, y posibilidad de flujos conversacionales

**Justificación de no implementarlo**: 
El flujo actual es lineal (no conversacional) y completa en una única ejecución, por lo que la persistencia de estado no aportaba valor al MVP. Para flujos de ida y vuelta con usuarios o procesos largos con múltiples reintentos, sería fundamental.

### 🔐 Autenticación y Autorización

**Estado actual**: Los endpoints son públicos y no requieren autenticación.

**Mejora propuesta**:
- **Opción 1**: Django Session Authentication (integrado con admin)
- **Opción 2**: JWT (JSON Web Tokens) con `djangorestframework-simplejwt`
- **Opción 3**: API Keys para integraciones externas
- Implementar permisos por usuario (rate limiting, quotas de uso)

**Justificación de no implementarlo**: 
Para el alcance del challenge no se especificó la necesidad de autenticación. En producción sería crítico para:
- Control de acceso y seguridad
- Rate limiting por usuario
- Tracking de uso y costos de API
- Compliance y auditoría


### 📊 Otras Mejoras Potenciales

| Mejora | Descripción | Prioridad |
|--------|-------------|-----------|
| **Webhooks** | Notificaciones cuando el análisis finaliza (útil para videos largos) | Media |
| **Queue System** | Celery + Redis para procesamiento asíncrono real | Alta |
| **Caching** | Redis para cachear resultados de videos ya analizados | Media |
| **Monitoring** | Sentry para error tracking, Prometheus para métricas | Alta |
| **API Versioning** | `/api/v1/analyze/` para mantener compatibilidad | Baja |
| **Bulk Processing** | Endpoint para analizar múltiples videos en batch | Media |
| **Streaming Responses** | Server-Sent Events para progreso en tiempo real | Baja |

---

## 📝 Conclusión

El proyecto implementa una solución completa y funcional que cumple con todos los requisitos del challenge:
- ✅ Arquitectura de agentes con LangGraph
- ✅ Extracción, análisis y estructuración de videos
- ✅ Persistencia en PostgreSQL
- ✅ Manejo robusto de errores
- ✅ Clean code y buenas prácticas
- ✅ Dockerización completa
- ✅ Tests de casos principales

Las mejoras sugeridas (persistencia de agentes, autenticación) son decisiones arquitectónicas conscientes que se omitieron por estar fuera del alcance del MVP, pero que están claramente identificadas y documentadas para implementación futura en un entorno productivo
