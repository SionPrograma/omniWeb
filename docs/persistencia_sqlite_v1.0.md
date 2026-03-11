# Infraestructura de Persistencia SQLite (v1.0)

Este documento describe la base de datos centralizada y reutilizable introducida en OmniWeb para migrar de almacenamiento en memoria a persistencia definitiva.

## 1. Estrategia de Almacenamiento

Se ha optado por **SQLite** como motor de persistencia debido a:
- Cero configuración (archivo local).
- Portabilidad (consistente con el enfoque "Portable First").
- Rendimiento suficiente para una plataforma personal.

El archivo de base de datos se ubica por defecto en:
`backend/data/omniweb.db`

## 2. Componentes de la Infraestructura

### `backend/core/database.py`
Provee la clase `DatabaseManager` que centraliza:
- Creación automática del directorio de datos si no existe.
- Gestión de conexiones (`get_connection()`).
- Configuración de `sqlite3.Row` para acceso por nombre de columna.

### `backend/core/config.py`
Define las variables de entorno/configuración:
- `DATA_DIR`: Directorio base para archivos de datos.
- `DATABASE_NAME`: Nombre del archivo `.db`.
- `DATABASE_URL`: Ruta absoluta generada.

## 3. Guía de Uso para Chips

Los chips híbridos deben evitar crear sus propios archivos `.db` individuales. En su lugar, deben utilizar la infraestructura común:

```python
from backend.core.database import db_manager

def get_my_data():
    conn = db_manager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM my_chip_table")
        return cursor.fetchall()
    finally:
        conn.close()
```

### Inicialización de Tablas (Propuesto)
Cada chip es responsable de inicializar sus propias tablas. Se recomienda seguir un patrón de "Repository":
1. Crear `chips/chip-{nombre}/core/repository.py`.
2. Incluir un método `init_tables()` que ejecute `CREATE TABLE IF NOT EXISTS`.
3. Llamar a este método durante la carga del chip o en el primer acceso.

## 4. Evolución
Esta fase prepara el terreno para:
- Reemplazar los `MOCK_DB` en memoria por consultas reales.
- Implementar migraciones simples.
- Centralizar backups del ecosistema OmniWeb simplemente copiando la carpeta `backend/data/`.
