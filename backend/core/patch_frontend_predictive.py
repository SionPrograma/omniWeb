import codecs
import os

def patch_frontend_predictive():
    js_path = 'frontend/shell/main_new.js'
    
    with codecs.open(js_path, 'r', 'utf-16') as f:
        content = f.read()

    # 1. UI CSS for Predictive Cards
    css_patch = """
/* OMNIWEB — PREDICTIVE ADVISOR STYLES */
.predictive-card {
    background: rgba(45, 0, 90, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: 12px;
    padding: 1.25rem;
    position: relative;
    overflow: hidden;
}
.predictive-state-badge {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.65rem;
    font-weight: 900;
}
.state-HIGH_DRIFT_PROBABILITY { background: #F97316; color: white; }
.state-PREVENTIVE_ACTION_RECOMMENDED { background: #EF4444; color: white; animation: pulseRed 2s infinite; }
.state-WATCH_CLOSELY { background: #8B5CF6; color: white; }

.predictive-confidence {
    position: absolute;
    top: 1.25rem;
    right: 1.25rem;
    font-size: 0.75rem;
    font-weight: 800;
    color: var(--accent);
}
"""
    # Append to creator.css in a previous step, but let's just inject in main_new.js for quickness if needed
    # Actually, I'll append to creator.css first.
    with open('frontend/shell/creator.css', 'a') as f:
        f.write(css_patch)

    # 2. JS: renderPredictiveAdvisor function
    predictive_js = """
    async function renderPredictiveAdvisor() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">CALCULANDO DERIVA PREDICTIVA...</h1></div>`;

        try {
            const res = await fetch('/api/v1/governance/predictive/active');
            const data = await res.json();
            const advisories = data.payload || [];

            let html = `
                <div class="forensic-cockpit-container" style="animation: omniSlideUp 0.4s ease;">
                    <button class="forensic-back-btn" onclick="window.omniShell.switchView('workspace')">← VOLVER AL CREATOR</button>
                    <div class="forensic-header">
                        <h1>PREDICTIVE DRIFT ADVISOR</h1>
                        <p class="forensic-description">Anticipación táctica basada en patrones históricos de Learning Surface y Deuda Viva.</p>
                    </div>
            `;

            if (advisories.length === 0) {
                html += `<div style="padding: 3rem; text-align: center; opacity: 0.5;"><h3>SISTEMA ESTABLE. No se detectan señales de deriva predictiva fuerte.</h3></div>`;
            } else {
                html += `<div class="learning-grid">`;
                advisories.forEach(adv => {
                    html += `
                        <div class="predictive-card">
                            <div class="predictive-confidence">${Math.round(adv.confidence * 100)}% CONFITUDE</div>
                            <span class="predictive-state-badge state-${adv.predictive_state}">${adv.predictive_state}</span>
                            <h3 style="margin: 1rem 0 0.5rem 0;">Dominio: ${adv.target_domain}</h3>
                            <p style="font-size: 0.85rem; color: var(--text-secondary);">${adv.rationale}</p>
                            <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; margin: 1rem 0;">
                                <strong style="font-size: 0.7rem; color: var(--accent); text-transform: uppercase;">Proyección de Riesgo:</strong>
                                <p style="margin: 4px 0; font-size: 0.85rem;">${adv.risk_projection}</p>
                            </div>
                            <div style="border-top: 1px solid var(--border-subtle); padding-top: 1rem; margin-top: 1rem;">
                                <strong style="font-size: 0.7rem; color: #ffcc00; text-transform: uppercase;">Recomendación Preventiva:</strong>
                                <p style="margin: 4px 0; font-size: 0.85rem; font-weight: 700;">${adv.recommended_action}</p>
                            </div>
                            <div style="display: flex; gap: 10px; margin-top: 1.5rem;">
                                <button class="forensic-action-btn" onclick="window.omniRenderFrictionHeatmap()">AUDITAR HOTSPOT</button>
                                <button class="forensic-action-btn secondary" onclick="window.omniRenderLearningSurface()">LECCIONES RELACIONADAS</button>
                            </div>
                        </div>
                    `;
                });
                html += `</div>`;
            }

            html += `</div>`;
            mainContent.innerHTML = html;
        } catch (e) {
            mainContent.innerHTML = `<div class="forensic-cockpit-container"><h3 style="color:red;">Error en Drif Scan.</h3></div>`;
        }
    }
    window.omniRenderPredictiveAdvisor = renderPredictiveAdvisor;
    """

    # Inject into main_new.js near exports
    marker = 'window.omniRenderForensicCockpit = renderForensicCockpit;'
    if marker in content:
        content = content.replace(marker, marker + "\n" + predictive_js)
        
        # Also update Mobile Quick Actions to include Predictive
        # I'll update the renderMobileQuickActions function I added in V2.
        old_mobile_btn = '<span>LEARNING</span>'
        new_mobile_btn = '<span>LEARNING</span></button><button class="mobile-action-btn" onclick="window.omniRenderPredictiveAdvisor()">${summary.predictive_signals > 0 ? `<div class="mobile-badge">${summary.predictive_signals}</div>` : ""}<span class="icon">⚥</span><span>DRIFT</span>'
        
        if old_mobile_btn in content:
            content = content.replace(old_mobile_btn, new_mobile_btn)

        with codecs.open(js_path, 'w', 'utf-16') as f:
            f.write(content)
        print("Frontend Predictive Advisor UI patched.")
    else:
        print("Marker missing in main_new.js.")

if __name__ == "__main__":
    patch_frontend_predictive()
