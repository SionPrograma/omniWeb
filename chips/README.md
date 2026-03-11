# OmniWeb Chips (Ecosistema v1.0)

Estructura modular de funcionalidades ("chips") independientes. Para más detalles técnicos, consulta el [Contrato Técnico de Chips](file:///docs/contrato_tecnico_chips_v1.0.md).

## Clasificación de Chips Actuales

| Chip | Categoría | Descripción |
| :--- | :--- | :--- |
| `chip-reparto` | **Híbrido** | Logística con mapa y backend de paradas. |
| `chip-finanzas` | **Híbrido** | Control financiero con API de transacciones. |
| `chip-idiomas-ia` | **Frontend-only** | Interfaz de tutor de idiomas (Backend legacy en `modules/`). |
| `chip-programacion`| **Frontend-only** | Mentoría de código con layouts interactivos. |
| `chip-musica` | **Placeholder** | Roadmap de teoría y práctica musical (Sin UI activa). |

> **Nota:** El servidor Backend (`backend/main.py`) orquestra la carga dinámica de estos chips basándose en su estructura de carpetas.

