# Frontend Global Dashboard (`frontend/`)

> **⚠️ AVISO ESTRUCTURAL IMPORTANTE:**
> A diferencia de proyectos React/SPA donde esta carpeta contaría TODAS las páginas e interfaces de las apps, **en la arquitectura de OmniWeb v0.2.0, esta carpeta SOLO tiene bajo responsabilidad el Dashboard o Portal Central de Entrada o Shell UI (que levanta `/`)**.

## Convenciones de Uso
1. **Punto Único**: Este directorio tiene esencialmente un `index.html` estático del menú raíz (portal galáctico o hub).
2. **Chips Visuales Individuales**: El código de UI aislado para *Finanzas*, *Programación* y otros, debe vivir estructuradamente dentro de `chips/chip-{nombre}/frontend`, NO aquí.
3. No deben alojarse componentes JS sueltos no concernientes al dashboard en esta ruta. Para compartir lógica puramente cliente con los demás chips, usa la raíz **`core/`**.
