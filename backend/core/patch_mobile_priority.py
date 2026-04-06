import codecs
import os

def final_mobile_priority_patch():
    js_path = 'frontend/shell/main_new.js'
    
    with codecs.open(js_path, 'r', 'utf-16') as f:
        content = f.read()

    # 1. Update Heatmap to sort by friction_score DESC on mobile
    heatmap_marker = 'const heatmap = await res.json();'
    heatmap_sort_js = """
            let heatmap = await res.json();
            if (window.innerWidth <= 768) {
                heatmap.sort((a, b) => b.friction_score - a.friction_score); // Priority sorting for Mobile
            }
    """
    if heatmap_marker in content:
        content = content.replace(heatmap_marker, heatmap_sort_js)

    # 2. Add 'Back to Creator' always at the top for Heatmap/Forensic on Mobile
    # I already added it for Forensic/Learning in the previous pass.
    # Now I add it to Heatmap too.
    heatmap_html_start = 'mainContent.innerHTML = html;'
    mobile_return_js = """
            if (window.innerWidth <= 768) {
                const returnBtn = document.createElement('button');
                returnBtn.className = 'mobile-return-btn';
                returnBtn.innerText = 'VOLVER';
                returnBtn.onclick = () => window.omniShell.switchView('workspace');
                mainContent.prepend(returnBtn);
            }
    """
    # Find the specific renderFrictionHeatmap start point
    heatmap_func_start = content.find('async function renderFrictionHeatmap()')
    if heatmap_func_start != -1:
        insert_pos = content.find(heatmap_html_start, heatmap_func_start)
        if insert_pos != -1:
             content = content[:insert_pos] + mobile_return_js + content[insert_pos:]

    with codecs.open(js_path, 'w', 'utf-16') as f:
        f.write(content)
    print("Frontend Mobile Priority Sorting & Navigation patched.")

if __name__ == "__main__":
    final_mobile_priority_patch()
