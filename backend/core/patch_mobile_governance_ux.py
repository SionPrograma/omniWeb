import codecs
import os

def patch_mobile_ux():
    js_path = 'frontend/shell/main_new.js'
    css_path = 'frontend/shell/creator.css'
    
    # 1. CSS PATCH - Mobile Overrides
    mobile_css = """
/* OMNIWEB — MOBILE UX GOVERNANCE PASS */
@media screen and (max-width: 768px) {
    /* 1. Cockpits & Grid Adaptations */
    .forensic-summary-row, .learning-grid, .heatmap-grid {
        grid-template-columns: 1fr !important;
        gap: 1rem !important;
    }
    
    .forensic-card, .learning-item-card, .autopsy-card {
        padding: 1rem !important;
        border-radius: 8px !important;
    }
    
    .card-value {
        font-size: 1.5rem !important;
    }
    
    /* 2. Modal Refinement */
    .governance-modal-content {
        width: 95% !important;
        padding: 1rem !important;
        max-height: 90vh !important;
        overflow-y: auto !important;
    }
    
    .modal-actions {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .modal-actions button {
        width: 100%;
        padding: 12px !important;
    }

    /* 3. Mobile Quick Actions Bar */
    .mobile-quick-actions {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(10, 10, 15, 0.95);
        backdrop-filter: blur(20px);
        border-top: 1px solid var(--accent-transparent);
        display: flex;
        justify-content: space-around;
        padding: 10px 0;
        z-index: 9999;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.5);
    }
    
    .mobile-action-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        color: var(--text-muted);
        background: none;
        border: none;
        font-size: 0.65rem;
        font-weight: 700;
        cursor: pointer;
    }
    
    .mobile-action-btn.active {
        color: var(--accent);
    }
    
    .mobile-action-btn .icon {
        font-size: 1.2rem;
        margin-bottom: 2px;
    }

    /* 4. Trace Table -> Card Transformation */
    .forensic-trace-table {
        display: block;
    }
    .forensic-trace-table thead {
        display: none;
    }
    .forensic-trace-table tr {
        display: flex;
        flex-direction: column;
        background: rgba(255,255,255,0.03);
        margin-bottom: 1rem;
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 1rem;
    }
    .forensic-trace-table td {
        display: block;
        padding: 4px 0 !important;
        border: none !important;
    }
    .trace-cell-id::before { content: "ID: "; opacity: 0.5; }
    .trace-cell-domain::before { content: "DOMAIN: "; opacity: 0.5; }
    
    /* 5. HUD Spacer */
    body { padding-bottom: 70px; }
}
"""
    with open(css_path, 'a') as f:
        f.write(mobile_css)
        
    # 2. JS PATCH - Mobile Logic (MAIN_NEW.JS)
    with codecs.open(js_path, 'r', 'utf-16') as f:
        content = f.read()

    # Inject Mobile Quick Actions Bar Renderer
    mobile_bar_js = """
    function renderMobileQuickActions() {
        if (window.innerWidth > 768) return;
        
        // Remove existing if any
        const existing = document.getElementById('omni-mobile-actions');
        if (existing) existing.remove();
        
        const bar = document.createElement('div');
        bar.id = 'omni-mobile-actions';
        bar.className = 'mobile-quick-actions';
        bar.innerHTML = `
            <button class="mobile-action-btn" onclick="window.omniRenderForensicCockpit()">
                <span class="icon">⬚</span>
                <span>COCKPIT</span>
            </button>
            <button class="mobile-action-btn" onclick="window.omniRenderFrictionHeatmap()">
                <span class="icon">◎</span>
                <span>HEATMAP</span>
            </button>
            <button class="mobile-action-btn" onclick="window.omniRenderLearningSurface()">
                <span class="icon">★</span>
                <span>LEARNING</span>
            </button>
            <button class="mobile-action-btn highlight" onclick="window.omniShell.switchView('workspace')">
                <span class="icon">✦</span>
                <span>CREATOR</span>
            </button>
        `;
        document.body.appendChild(bar);
    }
    
    // Call on load and resize
    window.addEventListener('resize', renderMobileQuickActions);
    setTimeout(renderMobileQuickActions, 1000);
    """
    
    # Insert before the end of the script (or near existing exports)
    marker = 'window.omniRenderForensicCockpit = renderForensicCockpit;'
    if marker in content:
        content = content.replace(marker, marker + "\n" + mobile_bar_js)
        with codecs.open(js_path, 'w', 'utf-16') as f:
            f.write(content)
        print("Frontend Mobile Optimization patched.")
    else:
        print("Marker missing in main_new.js.")

if __name__ == "__main__":
    patch_mobile_ux()
