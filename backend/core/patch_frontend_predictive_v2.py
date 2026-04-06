import codecs
import os

def patch_frontend_predictive_v2():
    js_path = 'frontend/shell/main_new.js'
    
    with codecs.open(js_path, 'r', 'utf-16') as f:
        content = f.read()

    # JS Entscheidung Funktion
    decision_js = """
    async function takePredictiveDecision(advId, decision) {
        try {
            const res = await fetch('/api/v1/governance/predictive/advisories/' + advId + '/decision?decision=' + decision, { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                window.omniRenderPredictiveAdvisor();
            } else {
                alert("Error: " + data.message);
            }
        } catch (e) {
            console.error("Decision failed", e);
        }
    }
    window.omniTakePredictiveDecision = takePredictiveDecision;
    """

    # Ersetzen der Buttons in renderPredictiveAdvisor
    # Wir suchen nach der Vorlage in renderPredictiveAdvisor
    old_btns = '<button class="forensic-action-btn" onclick="window.omniRenderFrictionHeatmap()">AUDITAR HOTSPOT</button>'
    new_btns = (
        '<button class="forensic-action-btn" onclick="window.omniRenderFrictionHeatmap()">AUDITAR HOTSPOT</button>' +
        '<button class="forensic-action-btn" style="background:#10B981;" onclick="window.omniTakePredictiveDecision(\'${adv.advisory_id}\', \'ACT_PREVENTIVELY\')">ACTUAR PREVENTIVAMENTE</button>' +
        '<button class="forensic-action-btn secondary" onclick="window.omniTakePredictiveDecision(\'${adv.advisory_id}\', \'POSTPONE\')">POSTERGAR</button>'
    )

    if old_btns in content:
        content = content.replace(old_btns, new_btns)
        # Auch Export hinzufügen
        marker = 'window.omniRenderPredictiveAdvisor = renderPredictiveAdvisor;'
        if marker in content and 'omniTakePredictiveDecision' not in content:
            content = content.replace(marker, marker + "\n" + decision_js)

        with codecs.open(js_path, 'w', 'utf-16') as f:
            f.write(content)
        print("Frontend Predictive Advisor V2 patched successfully.")
    else:
        print("Buttons marker not found in main_new.js.")

if __name__ == "__main__":
    patch_frontend_predictive_v2()
