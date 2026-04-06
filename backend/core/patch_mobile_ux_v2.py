import codecs
import os

def patch_mobile_ux_v2():
    js_path = 'frontend/shell/main_new.js'
    css_path = 'frontend/shell/creator.css'
    
    # 1. CSS - Mobile Badge & Top Banner
    css_extra = """
/* OMNIWEB — MOBILE UX V2: PRIORITY & BADGES */
@media screen and (max-width: 768px) {
    .mobile-action-btn { position: relative; }
    .mobile-badge {
        position: absolute;
        top: -5px;
        right: 0px;
        background: #EF4444;
        color: white;
        border-radius: 50%;
        width: 16px;
        height: 16px;
        font-size: 0.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--bg-primary);
        font-weight: 900;
        animation: badgePop 0.3s ease;
    }
    
    .mobile-critical-banner {
        position: fixed;
        top: 40px;
        left: 0;
        width: 100%;
        background: rgba(239, 68, 68, 0.9);
        color: white;
        text-align: center;
        padding: 5px;
        font-size: 0.65rem;
        font-weight: bold;
        z-index: 10002;
        letter-spacing: 0.5px;
    }

    @keyframes badgePop { 0% { transform: scale(0); } 100% { transform: scale(1); } }
}
"""
    with open(css_path, 'a') as f:
        f.write(css_extra)

    # 2. JS - Enhance Mobile Bar with Live Data
    with codecs.open(js_path, 'r', 'utf-16') as f:
        content = f.read()

    # Re-implement rendering function with fetch
    enhanced_bar_js = """
    async function renderMobileQuickActions() {
        if (window.innerWidth > 768) {
            const bar = document.getElementById('omni-mobile-actions');
            if (bar) bar.remove();
            return;
        }
        
        let summary = { critical_hotspots: 0, pending_proposals: 0, pending_outcomes: 0 };
        try {
            const res = await fetch('/api/v1/governance/mobile/summary');
            const data = await res.json();
            if (data.payload) summary = data.payload;
        } catch (e) { console.warn("Failed mobile summary fetch."); }
        
        // Remove existing if any
        let bar = document.getElementById('omni-mobile-actions');
        if (!bar) {
            bar = document.createElement('div');
            bar.id = 'omni-mobile-actions';
            bar.className = 'mobile-quick-actions';
            document.body.appendChild(bar);
        }
        
        bar.innerHTML = `
            <button class="mobile-action-btn" onclick="window.omniRenderForensicCockpit()">
                ${summary.pending_outcomes > 0 ? `<div class="mobile-badge">${summary.pending_outcomes}</div>` : ''}
                <span class="icon">⬚</span>
                <span>COCKPIT</span>
            </button>
            <button class="mobile-action-btn" onclick="window.omniRenderFrictionHeatmap()">
                ${summary.critical_hotspots > 0 ? `<div class="mobile-badge">${summary.critical_hotspots}</div>` : ''}
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

        // Render Critical Banner if needed
        const oldBanner = document.getElementById('omni-mobile-critical-banner');
        if (oldBanner) oldBanner.remove();

        if (summary.max_severity >= 80) {
            const banner = document.createElement('div');
            banner.id = 'omni-mobile-critical-banner';
            banner.className = 'mobile-critical-banner';
            banner.innerHTML = `⚠️ RIESGO CRÍTICO DETECTADO: FRICCIÓN AL ${Math.round(summary.max_severity)}%`;
            document.body.appendChild(banner);
        }
    }
    
    // Call on load and periodically
    window.addEventListener('resize', renderMobileQuickActions);
    setInterval(renderMobileQuickActions, 15000); // Check every 15s
    setTimeout(renderMobileQuickActions, 1500);
    """
    
    # Direct replacement of the old renderMobileQuickActions function
    start_tag = 'function renderMobileQuickActions() {'
    end_tag = 'setTimeout(renderMobileQuickActions, 1000);'
    
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag) + len(end_tag)
    
    if start_idx != -1:
        content = content[:start_idx] + enhanced_bar_js + content[end_idx:]
        with codecs.open(js_path, 'w', 'utf-16') as f:
            f.write(content)
        print("Frontend Mobile UX V2 (Priority & Badges) patched.")
    else:
        print("Marker missing in main_new.js.")

if __name__ == "__main__":
    patch_mobile_ux_v2()
