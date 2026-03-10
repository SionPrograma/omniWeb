# Informe de Fase 03: Validación de Acceso Local (Lingua)

Se ha completado la validación del arranque local de OmniWeb y el acceso al módulo Lingua. Siguiendo las reglas de mantener el sistema liviano y realizar cambios mínimos, se han optimizado los servicios para permitir un inicio exitoso del servidor incluso en entornos sin las dependencias pesadas de IA instaladas.

## 1. Comando exacto para arrancar OmniWeb

El backend está configurado como un paquete de Python. El comando recomendado para iniciarlo desde la raíz del proyecto es:

```bash
python -m backend.main
```

Alternativamente, se puede usar `uvicorn` directamente:
```bash
uvicorn backend.main:app --reload --port 8000
```

## 2. URLs de acceso local

Una vez que el servidor está corriendo (por defecto en el puerto 8000):

*   **Raíz de la plataforma:** [http://localhost:8000/](http://localhost:8000/)
    *   *Respuesta:* JSON con el nombre del proyecto, versión y lista de módulos activos (confirmado que incluye `lingua`).
*   **Interfaz de Lingua:** [http://localhost:8000/lingua/](http://localhost:8000/lingua/)
    *   *Respuesta:* Carga del `index.html` del módulo con todos sus estilos y scripts.
*   **API del módulo Lingua:** [http://localhost:8000/api/v1/lingua/process/](http://localhost:8000/api/v1/lingua/process/)
    *   *Respuesta:* El endpoint está registrado y listo para recibir peticiones POST.

## 3. Cambios realizados (Mapeo de archivos)

Para cumplir con el objetivo de "arranque liviano" y evitar errores por dependencias faltantes durante el registro de módulos:

| Archivo | Cambio Realizado | Razón |
| :--- | :--- | :--- |
| `modules/lingua/services/transcriber.py` | Importaciones de `whisper` y `torch` movidas al interior de los métodos (lazy loading). | Evitar fallos de arranque si no están instalados; no consumir RAM hasta que se use la transcripción. |
| `modules/lingua/services/tts_generator.py` | Importaciones de `TTS` y `torch` movidas al interior de los métodos. | Idem anterior. Mantiene el core de la plataforma ligero. |

## 4. Limitaciones detectadas

1.  **Dependencias de Procesamiento:** Aunque el backend inicia y la UI carga, los procesos de transcripción y TTS fallarán si no se instalan las dependencias indicadas en `requirements.txt` (`openai-whisper`, `TTS`, `torch`). Se recomienda instalarlas solo cuando se desee probar el flujo completo.
2.  **FFmpeg:** Se requiere que `ffmpeg` esté instalado en el sistema (path de Windows) para la extracción de audio y mezcla de video, aunque esto no impide el arranque del servidor.
3.  **Barra inclinada (Slash):** Para acceder a la UI de Lingua es preferible usar la ruta con barra al final (`/lingua/`) para asegurar que las referencias relativas a archivos CSS/JS se resuelvan correctamente.

## Resultado Final
OmniWeb está ahora validado como plataforma capaz de servir su núcleo y sus módulos (chips) de forma independiente y segura. Lingua es el primer módulo plenamente accesible desde el navegador.
