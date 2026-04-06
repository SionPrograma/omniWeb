import codecs
import json
import os

def patch_frontend_learning():
    js_path = 'frontend/shell/main_new.js'
    css_path = 'frontend/shell/forensic_cockpit.css'
    
    # 1. CSS PATCH
    css_extra = """
/* Learning Surface Section */
.learning-surface-container {
    padding: 2rem;
    animation: fadeIn 0.4s ease-out;
}

.learning-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.learning-item-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    border-top: 4px solid var(--accent);
    transition: all 0.2s ease;
}

.learning-item-card.antipattern {
    border-top-color: #EF4444;
}

.learning-type-badge {
    font-size: 0.65rem;
    font-weight: 800;
    text-transform: uppercase;
    padding: 4px 8px;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    width: fit-content;
}

.learning-confidence-bar {
    height: 4px;
    background: #333;
    border-radius: 2px;
    width: 60%;
    margin-top: 0.5rem;
}

.confidence-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
}

.antipattern .confidence-fill { background: #EF4444; }

.learning-lesson {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.4;
    margin-bottom: 0.5rem;
}

.learning-behavior {
    font-size: 0.85rem;
    color: var(--text-secondary);
    background: rgba(255,255,255,0.03);
    padding: 0.75rem;
    border-radius: 6px;
    border: 1px dashed var(--border-subtle);
}

.learning-meta {
    font-size: 0.7rem;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
}
"""
    with open(css_path, 'a') as f:
        f.write(css_extra)
        
    # 2. JS PATCH (MAIN_NEW.JS - UTF-16)
    with codecs.open(js_path, 'r', 'utf-16') as f:
        content = f.read()

    # Add button to Forensic Cockpit
    btn_marker = '<div class="forensic-header">'
    new_btn = '<button class="secondary" onclick="window.omniRenderLearningSurface()" style="margin-left:auto; background:var(--bg-tertiary); border:1px solid var(--accent); color:var(--accent); padding:4px 12px; cursor:pointer;">VER SUPERFICIE DE APRENDIZAJE</button>'
    
    if btn_marker in content:
        content = content.replace(btn_marker, btn_marker + new_btn)
        
    # Append the learning surface renderer
    learning_js = """
    async function renderLearningSurface() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        mainContent.innerHTML = `<div class="learning-surface-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">CONSOLIDANDO APRENDIZAJE...</h1></div>`;

        try {
            // Trigger a fresh scan first
            await fetch('/api/v1/governance/learning/surface/scan', { method: 'POST' });
            
            const res = await fetch('/api/v1/governance/learning/surface');
            const data = await res.json();
            const items = data.payload || [];

            let html = `
            <div class="learning-surface-container">
                <div class="forensic-header">
                    <div>
                        <h1>GOVERNANCE LEARNING SURFACE</h1>
                        <p class="forensic-description">Consolidación de sabiduría táctica y patrones estructurales confirmados.</p>
                    </div>
                    <button class="secondary" onclick="window.omniRenderForensicCockpit()" style="margin-left:auto; background:var(--bg-tertiary); border:1px solid var(--text-muted); color:var(--text-muted); padding:4px 12px; cursor:pointer;">VOLVER AL COCKPIT</button>
                </div>

                <div class="learning-grid">
                    ${items.length === 0 ? '<p>No se han consolidado lecciones todavía. Requiere mayor historial de intervenciones.</p>' : 
                    items.map(l => `
                        <div class="learning-item-card ${l.is_antipattern ? 'antipattern' : ''}">
                            <div class="learning-meta">
                                <span class="learning-type-badge">${l.learning_type}</span>
                                <span>Confianza: ${Math.round(l.confidence * 100)}%</span>
                            </div>
                            <div class="learning-confidence-bar">
                                <div class="confidence-fill" style="width: ${l.confidence * 100}%"></div>
                            </div>
                            <div class="learning-lesson">${l.lesson_summary}</div>
                            <div class="learning-behavior">
                                <strong>RECOMENDACIÓN:</strong><br>${l.recommended_behavior}
                            </div>
                            <div class="learning-meta" style="border-top:1px solid rgba(255,255,255,0.05); padding-top:0.5rem; margin-top:auto;">
                                <span>Dominio: <strong>${l.target_domain}</strong></span>
                                <span>Evidencias: <strong>${l.occurrence_count}</strong></span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>`;

            mainContent.innerHTML = html;
        } catch (err) {
            console.error(err);
            mainContent.innerHTML = `<div>Error al cargar superficie de aprendizaje.</div>`;
        }
    }
    window.omniRenderLearningSurface = renderLearningSurface;
    """
    
    # Append to the end of main_new.js or before the end of the script block
    # We find where we exported renderForensicCockpit
    marker = 'window.omniRenderForensicCockpit = renderForensicCockpit;'
    if marker in content:
        content = content.replace(marker, marker + "\n" + learning_js)
        with codecs.open(js_path, 'w', 'utf-16') as f:
            f.write(content)
        print("Frontend patched successfully.")
    else:
        print("Marker not found in main_new.js.")

if __name__ == "__main__":
    patch_frontend_learning()
