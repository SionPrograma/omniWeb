import codecs
import json
import os

def final_mobile_ux_pass():
    js_path = 'frontend/shell/main_new.js'
    css_path = 'frontend/shell/creator.css'
    
    # 1. CSS - Final Mobile Polish
    css_extra = """
/* OMNIWEB — MOBILE UX HARMONY */
@media screen and (max-width: 768px) {
    #main-content {
        padding: 5px !important;
        margin-top: 40px !important;
    }
    
    .forensic-header h1, .learning-surface h1 {
        font-size: 1.2rem !important;
    }
    
    .forensic-description {
        font-size: 0.75rem !important;
    }
    
    /* Touch Target Optimization */
    button, .mobile-action-btn, .hotspot-pill, .outcome-badge {
        min-height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Quick Action Button for Mobile Forensic */
    .mobile-return-btn {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 10001;
        background: var(--bg-tertiary);
        border: 1px solid var(--accent);
        color: var(--accent);
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: bold;
    }
}
"""
    with open(css_path, 'a') as f:
        f.write(css_extra)

    # 2. JS - Inject Mobile Bar and Return Button
    with codecs.open(js_path, 'r', 'utf-16') as f:
        content = f.read()

    # Add Return Button to renderForensicCockpit
    # We find where it starts and insert it at the top of innerHTML
    marker = 'mainContent.innerHTML = html;'
    mobile_return_inject = """
            if (window.innerWidth <= 768) {
                const returnBtn = document.createElement('button');
                returnBtn.className = 'mobile-return-btn';
                returnBtn.innerText = 'VOLVER';
                returnBtn.onclick = () => window.omniShell.switchView('workspace');
                mainContent.prepend(returnBtn);
            }
    """
    
    if marker in content:
        # We need to be careful with the UTF-16 content.
        # I'll append it before 'mainContent.innerHTML = html;' inside renderForensicCockpit and renderLearningSurface
        content = content.replace(marker, mobile_return_inject + "\n" + marker)
        
        with codecs.open(js_path, 'w', 'utf-16') as f:
            f.write(content)
        print("Frontend Governance UX Hardened for Mobile.")
    else:
        print("Marker not found for placement.")

if __name__ == "__main__":
    final_mobile_ux_pass()
