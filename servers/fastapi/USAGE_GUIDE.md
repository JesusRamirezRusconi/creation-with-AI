# 🚀 Guía de Uso - Nueva Arquitectura

## Para Desarrolladores

### Agregar un Nuevo Endpoint

**Paso 1**: Agregar método al servicio correspondiente

```python
# infrastructure/services/presentation_service.py
class PresentationService:
    async def archive_presentation(self, presentation_id: UUID) -> None:
        """Archive a presentation."""
        presentation = await self.repository.get_by_id(presentation_id)
        if not presentation:
            raise PresentationNotFoundException(str(presentation_id))
        
        presentation.archived = True
        await self.repository.update(presentation)
```

**Paso 2**: Agregar endpoint usando DI

```python
# api/v1/ppt/endpoints/presentation.py
@PRESENTATION_ROUTER.post("/archive/{id}")
async def archive_presentation(
    id: UUID,
    presentation_service: PresentationService = Depends(get_presentation_service),
):
    """Archive a presentation."""
    try:
        set_request_id()
        logger.info(f"POST /archive/{id} - Archiving presentation")
        await presentation_service.archive_presentation(id)
        return {"status": "archived"}
    except PresentationNotFoundException as e:
        raise e.to_http_exception()
    except Exception as e:
        logger.exception("Failed to archive presentation")
        raise HTTPException(status_code=500, detail="Failed to archive")
```

**Paso 3**: Agregar test

```python
# tests/test_presentation_service.py
@pytest.mark.asyncio
async def test_archive_presentation(service, mock_repository):
    """Test archiving a presentation."""
    presentation_id = uuid4()
    mock_presentation = MagicMock()
    mock_repository.get_by_id.return_value = mock_presentation
    
    await service.archive_presentation(presentation_id)
    
    assert mock_presentation.archived is True
    mock_repository.update.assert_called_once()
```

### Agregar una Nueva Validación

**Paso 1**: Crear validador

```python
# domain/presentation/validators.py
def validate_max_file_size(files: List[str], max_size_mb: int = 50) -> None:
    """Validate that files don't exceed max size."""
    for file in files:
        size_mb = os.path.getsize(file) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise InvalidPresentationRequestException(
                f"File exceeds maximum size of {max_size_mb}MB",
                details={"file": file, "size_mb": size_mb},
            )
```

**Paso 2**: Usar en servicio

```python
# infrastructure/services/presentation_generation_service.py
async def generate_presentation(self, request: GeneratePresentationRequest):
    # Validate request
    await validate_presentation_request(request, self.session)
    
    # Nueva validación
    if request.files:
        validate_max_file_size(request.files, max_size_mb=50)
    
    # Continue...
```

### Crear una Nueva Excepción

```python
# core/exceptions.py
class PresentationQuotaExceededException(PresentationBaseException):
    """Raised when user exceeds presentation quota."""

    def __init__(self, current: int, max_allowed: int):
        super().__init__(
            message=f"Quota exceeded: {current}/{max_allowed} presentations",
            error_code="QUOTA_EXCEEDED",
            status_code=429,
            details={"current": current, "max_allowed": max_allowed},
        )
```

### Agregar Logging Contextual

```python
from core.logging import get_logger, log_with_context

logger = get_logger(__name__)

# Log simple
logger.info("Processing presentation")

# Log con contexto
log_with_context(
    logger,
    "info",
    "Processing presentation",
    presentation_id=str(presentation_id),
    n_slides=request.n_slides,
    language=request.language,
)
```

## Para Testing

### Ejecutar Tests

```bash
# Todos los tests
cd servers/fastapi
pytest tests/ -v

# Test específico
pytest tests/test_presentation_service.py -v

# Con coverage
pytest tests/ --cov=core --cov=domain --cov=infrastructure --cov-report=html

# Solo tests rápidos
pytest tests/ -m "not slow"
```

### Crear Mock de Servicio

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_presentation_service():
    service = AsyncMock()
    service.get_by_id.return_value = MagicMock()
    return service

@pytest.mark.asyncio
async def test_endpoint(mock_presentation_service):
    result = await mock_presentation_service.get_by_id(uuid4())
    assert result is not None
```

## Para Debugging

### Ver Logs Estructurados

Los logs ahora incluyen:
- `timestamp`: ISO 8601
- `request_id`: UUID único por request
- `level`: INFO, WARNING, ERROR
- `module`, `function`, `line`: Ubicación exacta
- Campos custom extras

```json
{
  "timestamp": "2026-04-16T23:45:00.000Z",
  "level": "ERROR",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Failed to generate presentation",
  "exception": "...",
  "presentation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Rastrear Request

```python
# En el endpoint
set_request_id()  # Genera UUID automático

# O con ID específico
set_request_id("custom-request-123")

# Obtener request_id actual
current_id = get_request_id()
```

## Patrones de Diseño Usados

### 1. Repository Pattern

```python
# Interface (domain)
class PresentationRepositoryProtocol(Protocol):
    async def get_by_id(self, id: UUID) -> Optional[PresentationModel]: ...

# Implementación (infrastructure)
class PresentationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[PresentationModel]:
        return await self.session.get(PresentationModel, id)
```

### 2. Service Layer

```python
class PresentationService:
    def __init__(self, repository: PresentationRepositoryProtocol):
        self.repository = repository
    
    async def get_by_id(self, id: UUID) -> PresentationWithSlides:
        presentation = await self.repository.get_with_slides(id)
        if not presentation:
            raise PresentationNotFoundException(str(id))
        return presentation
```

### 3. Dependency Injection

```python
# Factory
def get_presentation_service(
    repository: PresentationRepositoryProtocol = Depends(get_presentation_repository),
) -> PresentationService:
    return PresentationService(repository)

# Uso en endpoint
@router.get("/")
async def endpoint(
    service: PresentationService = Depends(get_presentation_service),
):
    return await service.method()
```

## Tips y Best Practices

### ✅ DO
- Usar dependency injection para servicios
- Loggear operaciones importantes con contexto
- Crear excepciones específicas para cada caso
- Escribir tests para cada servicio nuevo
- Mantener endpoints concisos (< 20 líneas)
- Usar type hints en todo el código

### ❌ DON'T
- No poner lógica de negocio en endpoints
- No usar `print()`, usar `logger` siempre
- No hacer queries directos en endpoints
- No crear servicios gigantes (> 300 líneas)
- No ignorar excepciones sin loggear
- No olvidar `set_request_id()` en endpoints

## Troubleshooting

### Error: ModuleNotFoundError

```bash
# Asegurarse de estar en el entorno correcto
cd servers/fastapi
source venv/bin/activate  # o el path correcto
pip install -r requirements.txt
```

### Error: Circular Import

Revisar que:
- Domain no importe de infrastructure
- Core no importe de domain ni infrastructure
- Usar `TYPE_CHECKING` para type hints si es necesario

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.services.something import Something
```

### Tests Fallan

```bash
# Limpiar cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Re-ejecutar
pytest tests/ -v --tb=short
```

## Recursos

- **Arquitectura**: `REFACTORING.md`
- **Resumen**: `ARCHITECTURE_SUMMARY.md`
- **Implementación**: `IMPLEMENTATION_COMPLETE.md`
- **Este archivo**: `USAGE_GUIDE.md`

---

**¿Dudas?** Consulta la documentación o revisa los tests como ejemplos. 🚀
