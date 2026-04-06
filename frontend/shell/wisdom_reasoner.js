/* OMNIWEB — BLOQUE: TACTICAL WISDOM REASONER FRONTEND LOGIC */

class WisdomReasonerUI {
    constructor() {
        this.suggestions = [];
        this.currentContext = null;
    }

    async analyzeCurrentContext(context = {}) {
        this.currentContext = context;
        const panel = document.getElementById('wisdom-reasoner-panel');
        if (!panel) return;

        try {
            // In a real scenario, this would detect context from the Workspace (active branch/mission)
            // If context is empty, we suggest a general 'refactor' context for demo/test purposes
            const probeContext = Object.keys(context).length > 0 ? context : {
                target_domain: "core",
                problem_type: "REFACTOR",
                risk_level: "HIGH"
            };

            const response = await fetch('/api/v1/governance/wisdom/reasoner/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}`
                },
                body: JSON.stringify(probeContext)
            });

            const data = await response.json();
            if (data.status === 'success') {
                this.suggestions = data.payload;
                this.renderSuggestions();
            }
        } catch (err) {
            console.error("Reasoner analysis failed:", err);
        }
    }

    renderSuggestions() {
        const panel = document.getElementById('wisdom-reasoner-panel');
        if (!panel) return;

        if (this.suggestions.length === 0) {
            panel.classList.remove('active');
            return;
        }

        panel.classList.add('active');
        panel.innerHTML = `
            <div class="reasoner-header">
                <div class="reasoner-title">
                    <span class="node-type-badge">WISDOM REASONER — CONTEXTUAL INSIGHTS</span>
                    <span>Sabiduría Relevante para tu contexto actual</span>
                </div>
                <button class="atlas-btn secondary close-panel-btn">Ocultar</button>
            </div>
            <div class="reasoner-grid">
                ${this.suggestions.map(s => this.renderSuggestionCard(s)).join('')}
            </div>
        `;

        panel.querySelector('.close-panel-btn').onclick = () => panel.classList.remove('active');

        panel.querySelectorAll('.reasoner-suggestion').forEach(card => {
            card.onclick = (e) => {
                if (e.target.classList.contains('btn-use-tactic')) return;
                const nodeId = card.dataset.nodeId;
                if (window.wisdomAtlas) {
                    window.wisdomAtlas.viewNodeDetail(nodeId);
                }
            };
        });

        panel.querySelectorAll('.btn-use-tactic').forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                const suggestionId = btn.dataset.suggestionId;
                const suggestion = this.suggestions.find(s => s.suggestion_id === suggestionId);
                if (suggestion) this.generateMissionDraft(suggestion);
            };
        });
    }

    renderSuggestionCard(s) {
        const typeClass = this._getTypeClass(s.reasoning_type);
        return `
            <div class="reasoner-suggestion ${typeClass}" data-node-id="${s.node_id}">
                <div class="suggestion-type ${typeClass}">${s.reasoning_type.replace(/_/g, ' ')}</div>
                <div class="suggestion-title">${s.title}</div>
                <div class="suggestion-rationale">${s.rationale}</div>
                <div class="suggestion-footer">
                    <span class="suggestion-confidence">Match: ${Math.round(s.match_score * 100)}% | Conf: ${Math.round(s.confidence * 100)}%</span>
                    <button class="btn-use-tactic" data-suggestion-id="${s.suggestion_id}">DRAFT MISIÓN</button>
                </div>
            </div>
        `;
    }

    _getTypeClass(type) {
        if (type.includes('HIGH')) return 'type-high';
        if (type.includes('WARN')) return 'type-warn';
        if (type.includes('TACTIC')) return 'type-tactic';
        return 'type-ref';
    }

    async generateMissionDraft(suggestion) {
        console.log("[REASONER] Generando draft de misión para:", suggestion.title);
        try {
            const response = await fetch('/api/v1/governance/wisdom/drafts/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}`
                },
                body: JSON.stringify({
                    suggestion: suggestion,
                    context: this.currentContext || { target_domain: "core", problem_type: "REFACTOR" }
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                const draft = data.payload;
                console.log("[REASONER] Draft recibido:", draft);

                // Switch to Intake Panel in Pizarrón Vivo
                if (window.pizarronUI) {
                    const mount = document.getElementById('ws-intake-mount');
                    const panel = document.getElementById('ws-panel-intake');
                    const toggle = document.querySelector('.ws-toggle[data-panel="intake"]');

                    // Map Draft to Pizarron Mission Format
                    const pDraft = {
                        handoff_id: draft.draft_id,
                        objective: draft.title,
                        goal: draft.objective,
                        surface_affected: draft.surface_affected,
                        constraints: draft.constraints,
                        risk_level: draft.risk_level,
                        execution_style: "with_confirmation",
                        wisdom_source: {
                            node_id: draft.source_node_id,
                            title: draft.title
                        }
                    };

                    window.pizarronUI.renderIntakePanel(mount, pDraft);

                    if (panel && !panel.classList.contains('active')) {
                        panel.classList.add('active');
                        if (toggle) toggle.classList.add('active');
                        if (window.creatorEnv) window.creatorEnv.updateGridLayout();
                    }
                }
            }
        } catch (err) {
            console.error("Draft generation failed:", err);
        }
    }
}

window.wisdomReasoner = new WisdomReasonerUI();
