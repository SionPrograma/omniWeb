# Patrón de Arquitectura Backend por Chip (v1.0)

Este documento define la estructura estándar para el desarrollo del backend de los chips híbridos en OmniWeb v0.3.0.

## 1. La Estructura de Capas (S.R.S.R)

Para garantizar el desacoplamiento y la mantenibilidad, cada chip híbrido debe organizar su subcarpeta `core/` siguiendo el patrón:

1.  **Schemas (`schemas.py`)**: Define los contratos de datos utilizando Pydantic. No contienen lógica, solo validación de tipos para entrada/salida.
2.  **Repository (`repository.py`)**: Única capa que interactúa con la base de datos (SQLite). Encapsula las consultas SQL y la inicialización de tablas.
3.  **Service (`service.py`)**: Contiene la lógica de negocio y orquestación. Coordina entre el repositorio y otras necesidades del chip.
4.  **Router (`router.py`)**: Capa de transporte (FastAPI). Define los endpoints HTTP, parámetros de ruta y utiliza el Servicio para procesar peticiones.

## 2. Mapa de Responsabilidades

| Capa | Responsabilidad | Depende de... |
| :--- | :--- | :--- |
| **Router** | HTTP, Status Codes, Params | `Service`, `Schemas` |
| **Service** | Lógica, Reglas de Negocio | `Repository`, `Schemas` |
| **Repository** | SQL, CRUD, Conexión DB | `db_manager` (Core), `Schemas` |
| **Schemas** | Estructuras de Datos | - |

## 3. Ejemplo de Implementación

### Definición en `repository.py`
```python
class MyRepository:
    def get_data(self):
        with db_manager.get_connection() as conn:
            # SQL puro
            return conn.execute("SELECT * FROM table").fetchall()
```

### Definición en `router.py`
```python
@router.get("/")
async def list_data():
    return my_service.get_processed_data()
```

## 4. Beneficios del Patrón
- **Testabilidad**: Es posible testear la lógica de negocio en `service.py` sin necesidad de levantar el servidor web.
- **Intercambiabilidad**: Si en el futuro se cambia SQLite por otra DB, solo se ve afectada la capa de `repository.py`.
- **Limpieza**: El orquestador `backend/main.py` solo necesita conocer el `router.py`, manteniendo el resto de la implementación encapsulada en el chip.
