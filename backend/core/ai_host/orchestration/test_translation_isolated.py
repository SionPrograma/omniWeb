
import sys
import os

# REPRODUCING THE LOGIC FROM mission_orchestrator.py to validate translation
# WITHOUT requiring the whole backend/sqlite3 setup.

class MissionPhase:
    def __init__(self, name: str, status: str = "PENDIENTE", detail: str = "", source: str = "text"):
        self.name = name
        self.status = status
        self.detail = detail
        self.source = source

class MissionOrchestratorMock:
    def __init__(self):
        self.phases = []
        self.is_voice = False

    def plan_mission(self, message, intent, interpretation, source="text"):
        self.phases = []
        self.is_voice = (source == "voice")
        mission = interpretation.get("structured_mission")
        if self.is_voice:
             self.phases.append(MissionPhase("VOICE_READY", "COMPLETADO", "Entrada natural persistente procesada.", source="voice"))
        obj = mission["objective"] if mission else "Misión técnica"
        self.phases.append(MissionPhase("OBJETIVO_ESTABLECIDO", "COMPLETADO", f"Intención: {obj}"))
        surfaces = ", ".join(mission["surface_affected"]) if mission else "Indeterminado"
        self.phases.append(MissionPhase("FOCO_TÉCNICO", "COMPLETADO", f"Superficie: [{surfaces}]"))
        if mission and mission["constraints"]:
             cons = " | ".join(mission["constraints"])
             self.phases.append(MissionPhase("LÍMITES_OPERATIVOS", "COMPLETADO", f"Restricciones: {cons}"))
        risk = mission["risk_level"].upper() if mission else "BAJO"
        if risk == "HIGH":
             self.phases.append(MissionPhase("COGNITIVE_GOVERNANCE_LOCK", "BLOQUEADO", "RIESGO ALTO: Requiere confirmación manual para cada paso.", source="governance"))
        else:
             self.phases.append(MissionPhase("EVALUACIÓN_RIESGO", "COMPLETADO", f"Nivel: {risk}"))
        style = mission["execution_style"] if mission else "standard"
        if "audit_first" in style:
             self.phases.append(MissionPhase("AUDITORÍA_PREVIA", "PROCESANDO", "Modo Inspección Activo. No se realizarán mutaciones sin reporte previo."))
        elif "surgical_patch" in style:
             self.phases.append(MissionPhase("PATCH_QUIRÚRGICO", "PROCESANDO", "Aplicando criterio de mínima intervención."))
        else:
             self.phases.append(MissionPhase("PLAN_DE_EJECUCIÓN", "PROCESANDO", "Generando pasos de implementación estándar."))
        if mission and mission["stop_conditions"]:
             stops = " | ".join(mission["stop_conditions"])
             self.phases.append(MissionPhase("CONDICIONES_DE_FRENO", "COMPLETADO", f"Escalar si: {stops}"))
        self.phases.append(MissionPhase("PREVIEW_VISUAL", "PENDIENTE", "Preparando diff para auditoría del creador."))
        conf = "CON_CONFIRMACIÓN" if (mission and "with_confirmation" in mission["execution_style"]) else "ESTÁNDAR"
        self.phases.append(MissionPhase("APLICACIÓN", "STANDBY", f"Puerta de salida: {conf}"))
        return self.phases

    def format_orchestration_report(self) -> str:
        header = "### OMNI_WORK_ORCHESTRATION"
        report = f"{header}\n\n"
        for i, phase in enumerate(self.phases, 1):
             mark = "✅" if phase.status == "COMPLETADO" else "🔄" if phase.status == "PROCESANDO" else "⏸️" if phase.status == "STANDBY" else "🚫" if phase.status == "BLOQUEADO" else "⏳"
             report += f"{i}. {mark} **{phase.name}** | {phase.status}\n   > {phase.detail}\n"
        return report

orchestrator = MissionOrchestratorMock()

# Mocking interpretations from Step 1 results
test_cases = [
    {
        "text": "Optimiza la latencia del shell sin romper el auth",
        "interp": {
            "structured_mission": {
                "objective": "la latencia del shell",
                "surface_affected": ["shell", "auth"],
                "constraints": ["romper el auth"],
                "stop_conditions": [],
                "risk_level": "high",
                "execution_style": "standard"
            }
        }
    },
    {
        "text": "Arreglá el dashboard móvil pero no toques el shell público",
        "interp": {
            "structured_mission": {
                "objective": "el dashboard móvil",
                "surface_affected": ["shell", "dashboard", "mobile"],
                "constraints": ["toques el shell público"],
                "stop_conditions": [],
                "risk_level": "medium",
                "execution_style": "standard"
            }
        }
    },
    {
        "text": "Auditá el creator mode, y si afecta core frená y avisame",
        "interp": {
            "structured_mission": {
                "objective": "el creator mode",
                "surface_affected": ["auth", "core", "creator"],
                "constraints": [],
                "stop_conditions": ["afecta core"],
                "risk_level": "high",
                "execution_style": "audit_first_with_confirmation"
            }
        }
    }
]

print("--- MISSION TRANSLATION VALIDATION (Isolated) ---")
for case in test_cases:
    orchestrator.plan_mission(case["text"], "intent", case["interp"])
    print(f"\nINPUT: {case['text']}")
    print(orchestrator.format_orchestration_report())
