const ui = {
    elements: {
        form: document.getElementById('translator-form'),
        urlInput: document.getElementById('youtube-url'),
        fileInput: document.getElementById('video-file'),
        dropZone: document.getElementById('drop-zone'),
        fileName: document.getElementById('file-name'),
        langSelect: document.getElementById('target-lang'),
        submitBtn: document.getElementById('submit-btn'),
        statusContainer: document.getElementById('status-container'),
        stagesList: document.getElementById('stages-list'),
        resultContainer: document.getElementById('result-container'),
        resultAudio: document.getElementById('result-audio'),
        downloadLink: document.getElementById('download-link'),
        logContent: document.getElementById('log-content'),
        clearLogsBtn: document.getElementById('clear-logs'),
        // V1.9 Governance UI
        toggleGovBtn: document.getElementById('toggle-governance'),
        govPanel: document.getElementById('governance-panel'),
        auditContent: document.getElementById('audit-content'),
        refreshAuditBtn: document.getElementById('refresh-audit'),
        exportBtn: document.getElementById('export-json-btn'),
        // Block 79 Forge HUD
        toggleForgeBtn: document.getElementById('toggle-forge'),
        forgePanel: document.getElementById('forge-panel'),
        forgeContent: document.getElementById('forge-stats-container')
    },

    currentJobId: null,
    currentLens: 'balanced',

    updateStages(progress) {
        if (!progress) return;
        this.elements.statusContainer.style.display = 'block';
        this.elements.stagesList.innerHTML = '';

        progress.forEach(stage => {
            const stageEl = document.createElement('div');
            stageEl.className = `stage-item ${stage.percent === 100 ? 'completed' : stage.percent > 0 ? 'processing' : ''}`;

            // Reveal Mode Truth (V1.6)
            let modeBadge = '';
            const msg = (stage.message || '').toUpperCase();
            if (msg.includes('REAL')) {
                modeBadge = '<span class="badge mode-real">REAL</span>';
            } else if (msg.includes('MOCK') || msg.includes('FALLBACK') || msg.includes('PASS_THROUGH')) {
                modeBadge = '<span class="badge mode-fallback">FALLBACK</span>';
            }

            stageEl.innerHTML = `
                <div class="stage-icon">
                    ${stage.percent === 100 ? '<i class="fas fa-check"></i>' : '<i class="fas fa-spinner fa-spin"></i>'}
                </div>
                <div class="stage-details">
                    <div class="stage-name">${stage.stage.replace(/_/g, ' ').toUpperCase()} ${modeBadge}</div>
                    <div class="stage-status">${stage.message || stage.status}</div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: ${stage.percent}%"></div>
                    </div>
                </div>
            `;
            this.elements.stagesList.appendChild(stageEl);
        });
    },

    updateAudit(purges) {
        this.elements.auditContent.innerHTML = '';
        if (!purges || purges.length === 0) {
            this.elements.auditContent.innerHTML = '<div class="log-entry info">No hay purgas registradas.</div>';
            return;
        }

        purges.forEach(item => {
            const entry = document.createElement('div');
            entry.className = 'log-entry warning';
            const date = new Date(item.purged_at).toLocaleString();
            entry.innerHTML = `
                <span style="opacity: 0.5;">[${date}]</span> 
                <strong>Job Purged:</strong> ${item.job_id.substring(0, 8)}... 
                (Reason: ${item.reason})
            `;
            this.elements.auditContent.appendChild(entry);
        });
    },

    addLog(message, type = 'info') {
        const entry = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString();
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span style="opacity: 0.5;">[${timestamp}]</span> ${message}`;
        this.elements.logContent.appendChild(entry);
        this.elements.logContent.scrollTop = this.elements.logContent.scrollHeight;
    },

    showResult(url, status = 'completed', errorMsg = '', isPurged = False) {
        this.elements.resultContainer.style.display = 'block';

        if (status === 'purged' || isPurged) {
            this.elements.resultContainer.style.background = 'rgba(239, 68, 68, 0.1)';
            this.elements.resultContainer.style.borderColor = 'var(--error)';
            const statusText = this.elements.resultContainer.querySelector('p');
            statusText.textContent = 'Media Purged (Retention Policy)';
            statusText.style.color = 'var(--error)';
            this.elements.resultAudio.style.display = 'none';
            this.elements.downloadLink.style.display = 'none';
            this.addLog('El Job existe en el historial purgado, pero el archivo ha sido eliminado.', 'warning');
            return;
        }

        this.elements.resultAudio.style.display = 'block';
        this.elements.downloadLink.style.display = 'inline-block';

        if (status === 'partial_success') {
            this.elements.resultContainer.style.background = 'rgba(245, 158, 11, 0.1)';
            this.elements.resultContainer.style.borderColor = '#f59e0b';
            const statusText = this.elements.resultContainer.querySelector('p');
            if (statusText) {
                statusText.textContent = 'Process completed with warnings';
                statusText.style.color = '#f59e0b';
            }
            this.addLog(`Process completed with warnings: ${errorMsg}`, 'warning');
        } else {
            this.elements.resultContainer.style.background = 'rgba(16, 185, 129, 0.1)';
            this.elements.resultContainer.style.borderColor = 'var(--success)';
            const statusText = this.elements.resultContainer.querySelector('p');
            if (statusText) {
                statusText.textContent = 'Processing Complete!';
                statusText.style.color = 'var(--success)';
            }
            this.addLog('Process completed successfully. Audio ready.', 'success');
        }

        const baseUrl = window.location.origin.includes('file://') ? 'http://localhost:8000' : window.location.origin;
        const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;

        this.elements.resultAudio.src = fullUrl;
        this.elements.downloadLink.href = fullUrl;
        this.elements.submitBtn.disabled = false;
        this.elements.submitBtn.innerHTML = '<span>Translate & Narrate</span>';
    },

    setLoading(isLoading) {
        this.elements.submitBtn.disabled = isLoading;
        if (isLoading) {
            this.elements.submitBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Initializing...';
            this.elements.resultContainer.style.display = 'none';
        }
    },

    updateForgeHUD(data, recommendations = null, currentRequests = null, affinities = null, synergies = null, debt = null, drift = null) {
        if (!data || !data.capabilities) return;
        this.elements.forgeContent.innerHTML = '';

        // 0.0 Strategic Lens Filter (V2.2)
        const filterBar = document.createElement('div');
        filterBar.style.display = 'flex';
        filterBar.style.gap = '5px';
        filterBar.style.marginBottom = '1.5rem';
        filterBar.style.padding = '5px';
        filterBar.style.background = 'rgba(255,255,255,0.03)';
        filterBar.style.borderRadius = '6px';

        const lenses = ['balanced', 'performance', 'privacy', 'reliability'];
        lenses.forEach(l => {
            const btn = document.createElement('button');
            btn.className = 'btn-text lens-filter-btn';
            btn.setAttribute('data-lens', l);
            btn.style.fontSize = '8px';
            btn.style.padding = '4px 8px';
            btn.style.borderRadius = '4px';
            btn.style.textTransform = 'uppercase';
            btn.style.cursor = 'pointer';
            btn.style.flex = '1';
            btn.style.border = '1px solid rgba(255,255,255,0.1)';

            if (this.currentLens === l) {
                btn.style.background = 'var(--accent-primary)';
                btn.style.color = 'white';
                btn.style.borderColor = 'var(--accent-primary)';
            } else {
                btn.style.background = 'transparent';
                btn.style.color = 'var(--text-dim)';
            }
            btn.innerText = l;
            filterBar.appendChild(btn);
        });
        this.elements.forgeContent.appendChild(filterBar);

        // 0.05 Render Tactical Structural Debt (V2.3)
        if (debt && debt.status === 'success' && debt.clusters.length > 0) {
            const debtSection = document.createElement('div');
            debtSection.style.marginBottom = '2rem';
            debtSection.innerHTML = `<h5 style="color:var(--error); font-size:10px; margin-bottom:8px; border-bottom:1px solid rgba(255,59,48,0.2); padding-bottom:4px;">
                <i class="fas fa-biohazard"></i> TACTICAL STRUCTURAL DEBT (WEAK POINTS)
            </h5>`;

            debt.clusters.forEach(c => {
                const cluster = document.createElement('div');
                cluster.style.background = c.severity === 'HIGH' ? 'rgba(255, 59, 48, 0.08)' : 'rgba(255, 159, 10, 0.08)';
                cluster.style.borderLeft = `3px solid ${c.severity === 'HIGH' ? 'var(--error)' : '#f59e0b'}`;
                cluster.style.padding = '10px';
                cluster.style.marginBottom = '8px';
                cluster.style.borderRadius = '2px';
                cluster.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:bold; font-size:11px; color:${c.severity === 'HIGH' ? 'var(--error)' : '#f6ad55'};">${c.title}</span>
                        <span style="font-size:9px; background:rgba(0,0,0,0.3); padding:2px 6px; border-radius:10px;">${c.occurrence_count} samples</span>
                    </div>
                    <div style="font-size:10px; opacity:0.9; margin-bottom:4px;">${c.capability} @ ${c.provider}</div>
                    <div style="font-size:9px; opacity:0.7; font-style:italic;">"${c.reasoning}"</div>
                `;
                debtSection.appendChild(cluster);
            });
            this.elements.forgeContent.appendChild(debtSection);
        }

        // 0.06 Render Strategic Drift (V2.4)
        if (drift && drift.status === 'success' && drift.advisories.length > 0) {
            const driftSection = document.createElement('div');
            driftSection.style.marginBottom = '2rem';
            driftSection.innerHTML = `<h5 style="color:#f59e0b; font-size:10px; margin-bottom:8px; border-bottom:1px solid rgba(245,158,11,0.2); padding-bottom:4px;">
                <i class="fas fa-exclamation-triangle"></i> STRATEGIC DRIFT ALERTS
            </h5>`;

            drift.advisories.forEach(a => {
                const card = document.createElement('div');
                card.style.background = 'rgba(245, 158, 11, 0.08)';
                card.style.borderLeft = `3px solid ${a.severity === 'HIGH' ? 'var(--error)' : '#f59e0b'}`;
                card.style.padding = '10px';
                card.style.marginBottom = '8px';
                card.style.borderRadius = '2px';
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:bold; font-size:11px; color:#f6ad55;">${a.capability.toUpperCase()} DRIFT</span>
                        <span style="font-size:8px; border:1px solid #f59e0b; padding:1px 4px; border-radius:3px; color:#f59e0b;">${a.severity}</span>
                    </div>
                    <div style="font-size:10px; margin-bottom:4px;">
                        <span style="opacity:0.7;">Active:</span> <code style="color:var(--error);">${a.active_provider}</code> 
                        <i class="fas fa-arrow-right" style="margin:0 5px; opacity:0.5;"></i>
                        <span style="opacity:0.7;">Best-Fit:</span> <code style="color:var(--success); border-bottom:1px dashed var(--success);">${a.recommended_provider}</code>
                    </div>
                    <div style="font-size:9px; opacity:0.8; line-height:1.2;">${a.reason}</div>
                `;
                driftSection.appendChild(card);
            });
            this.elements.forgeContent.appendChild(driftSection);
        }

        // 0.1 Render Context Affinities (V2.0)
        if (affinities && affinities.status === 'success' && affinities.affinities.length > 0) {
            const affinitySection = document.createElement('div');
            affinitySection.style.marginBottom = '2rem';
            affinitySection.innerHTML = `<h4 style="font-size:11px; color:#10b981; margin-bottom:0.8rem;"><i class="fas fa-brain"></i> CONTEXT AFFINITIES (STRATEGIC EXPERIENCE)</h4>`;

            affinities.affinities.forEach(aff => {
                const affCard = document.createElement('div');
                affCard.className = 'log-entry info';
                affCard.style.padding = '8px';
                affCard.style.fontSize = '9px';
                affCard.style.marginBottom = '6px';
                affCard.style.borderLeft = `3px solid ${aff.affinity_score > 0 ? '#10b981' : '#f43f5e'}`;

                const scoreColor = aff.affinity_score > 0.5 ? '#10b981' : (aff.affinity_score < 0 ? '#f43f5e' : '#f59e0b');

                affCard.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                        <strong>${aff.context_tag}</strong>
                        <span style="color:${scoreColor}; font-weight:bold;">${(aff.affinity_score * 100).toFixed(0)}% AFFINITY</span>
                    </div>
                    <div style="opacity:0.8;">Prefers: <b>${aff.provider_id}</b> | Trend: ${aff.outcome_trend} (n=${aff.sample_count})</div>
                `;
                affinitySection.appendChild(affCard);
            });
            this.elements.forgeContent.appendChild(affinitySection);
        }

        // 0.2 Render Cross-Domain Synergies (V2.1)
        if (synergies && synergies.status === 'success' && synergies.synergies.length > 0) {
            const synergySection = document.createElement('div');
            synergySection.style.marginBottom = '2rem';
            synergySection.innerHTML = `<h4 style="font-size:11px; color:#ec4899; margin-bottom:0.8rem;"><i class="fas fa-project-diagram"></i> CROSS-DOMAIN SYNERGY (TRANSFERABLE WISDOM)</h4>`;

            synergies.synergies.forEach(syn => {
                const synCard = document.createElement('div');
                synCard.className = 'log-entry info';
                synCard.style.padding = '8px';
                synCard.style.fontSize = '9px';
                synCard.style.marginBottom = '6px';
                synCard.style.borderLeft = `3px solid #ec4899`;

                synCard.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                        <strong>FROM: CHIP-${syn.source_chip.toUpperCase()}</strong>
                        <span style="color:#ec4899; font-weight:bold;">${(syn.strength * 100).toFixed(0)}% TRANSFERABLE</span>
                    </div>
                    <div style="margin-bottom:4px;">Context: <b>${syn.context_tag}</b> for <b>${syn.capability}</b></div>
                    <div style="opacity:0.8; font-style:italic;">"${syn.rationale}"</div>
                    <div style="margin-top:4px; font-weight:bold; color:#ec4899;">Candidate Tool: ${syn.suggested_provider_id}</div>
                `;
                synergySection.appendChild(synCard);
            });
            this.elements.forgeContent.appendChild(synergySection);
        }

        // 1. Render Strategic Recommendations (Block 80)
        if (recommendations && recommendations.recommendations && recommendations.recommendations.length > 0) {
            const recSection = document.createElement('div');
            recSection.style.marginBottom = '2rem';
            recSection.innerHTML = `<h4 style="font-size:11px; color:#facc15; margin-bottom:0.8rem;"><i class="fas fa-lightbulb"></i> STRATEGIC ADVISORY (CONTEXTUAL)</h4>`;

            recommendations.recommendations.forEach(rec => {
                const recCard = document.createElement('div');
                recCard.className = 'log-entry warning';
                recCard.style.padding = '10px';
                recCard.style.fontSize = '11px';
                recCard.style.marginBottom = '10px';
                recCard.style.background = 'rgba(250, 204, 21, 0.05)';

                const strengthLabel = rec.strength.toUpperCase();
                const strengthClass = rec.strength === 'strong' ? 'mode-real' : 'mode-fallback';

                recCard.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                         <span style="font-weight:700; color:var(--text-main);">${rec.capability.toUpperCase()} Preference</span>
                         <span class="badge ${strengthClass}">${strengthLabel}</span>
                    </div>
                    <div style="margin-bottom:5px; color:var(--accent-primary);">Suggested: <strong>${rec.suggested_provider}</strong></div>
                    <div style="margin-bottom:8px; opacity:0.9;">${rec.rationale}</div>
                    <div style="font-style:italic; border-top:1px solid rgba(255,255,255,0.05); padding-top:5px; margin-top:5px; font-size:10px; display:flex; justify-content:space-between; align-items:center;">
                        <span>${rec.tradeoff}</span>
                        <button class="btn-text request-swap-btn" 
                            data-cap="${rec.capability}" 
                            data-to="${rec.suggested_provider}"
                            data-rat="${rec.rationale}"
                            data-trade="${rec.tradeoff}"
                            data-strength="${rec.strength}"
                            style="color:#facc15; font-weight:700; border:1px solid #facc15; padding:2px 6px; cursor:pointer;">
                            REQUEST SWAP
                        </button>
                    </div>
                `;
                recSection.appendChild(recCard);
            });
            this.elements.forgeContent.appendChild(recSection);
        }

        // 2. Active Forge Directives (Block 81)
        if (currentRequests && currentRequests.requests && currentRequests.requests.length > 0) {
            const pending = currentRequests.requests.filter(r => r.status === 'PENDING');
            if (pending.length > 0) {
                const directiveSection = document.createElement('div');
                directiveSection.style.marginBottom = '2rem';
                directiveSection.innerHTML = `<h4 style="font-size:11px; color:var(--accent-secondary); margin-bottom:0.8rem;"><i class="fas fa-gavel"></i> PENDING FORGE DIRECTIVES</h4>`;

                pending.forEach(req => {
                    const reqCard = document.createElement('div');
                    reqCard.className = 'log-entry system';
                    reqCard.style.padding = '10px';
                    reqCard.style.fontSize = '10px';
                    reqCard.style.marginBottom = '10px';
                    reqCard.style.borderColor = 'var(--accent-secondary)';

                    reqCard.innerHTML = `
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <strong>ID: ${req.id} - ${req.capability.toUpperCase()}</strong>
                            <span class="badge mode-fallback">PENDING APPROVAL</span>
                        </div>
                        <div style="margin-bottom:5px;">Swap: <span style="opacity:0.6">${req.from_provider}</span> <i class="fas fa-arrow-right" style="font-size:8px;"></i> <strong style="color:var(--accent-primary)">${req.to_provider}</strong></div>
                        <div style="display:flex; gap:10px; margin-top:8px;">
                            <button class="btn-text apply-swap-btn" data-id="${req.id}" style="background:var(--accent-secondary); color:white; padding:4px 8px; border-radius:4px; cursor:pointer;">
                                <i class="fas fa-check"></i> APPROVE & APPLY
                            </button>
                        </div>
                    `;
                    directiveSection.appendChild(reqCard);
                });
                this.elements.forgeContent.appendChild(directiveSection);
            }

            const applied = currentRequests.requests.filter(r => r.status === 'APPLIED');
            if (applied.length > 0) {
                const historySection = document.createElement('div');
                historySection.style.marginBottom = '2rem';
                historySection.innerHTML = `<h4 style="font-size:11px; color:#a855f7; margin-bottom:0.8rem;"><i class="fas fa-history"></i> RESOLVED DIRECTIVES (STRATEGIC MEMORY)</h4>`;

                applied.forEach(req => {
                    const reqCard = document.createElement('div');
                    reqCard.className = 'log-entry info';
                    reqCard.style.padding = '10px';
                    reqCard.style.fontSize = '9px';
                    reqCard.style.marginBottom = '8px';
                    reqCard.style.opacity = '0.8';

                    reqCard.innerHTML = `
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <strong>ID: ${req.id} - ${req.capability.toUpperCase()}</strong>
                            <span style="color:#a855f7;">RESOLVED</span>
                        </div>
                        <div style="margin-bottom:6px;">${req.from_provider} <i class="fas fa-arrow-right"></i> ${req.to_provider}</div>
                        <button class="btn-text replay-swap-btn" data-id="${req.id}" style="border:1px solid #a855f7; color:#a855f7; padding:1px 5px; cursor:pointer;">
                            ANALYZE OUTCOME (AUTOPSY)
                        </button>
                    `;
                    historySection.appendChild(reqCard);
                });
                this.elements.forgeContent.appendChild(historySection);
            }
        }

        // 3. Render Comparative Oversight (Existing)
        Object.keys(data.capabilities).forEach(cap => {
            const capGroup = document.createElement('div');
            capGroup.style.marginBottom = '1.5rem';
            capGroup.innerHTML = `<h4 style="text-transform:uppercase; font-size:12px; margin-bottom:0.5rem; color:var(--accent-primary); border-bottom:1px solid rgba(56, 189, 248, 0.2)">${cap}</h4>`;

            const providers = data.capabilities[cap];
            Object.values(providers).forEach(p => {
                const card = document.createElement('div');
                card.className = 'log-entry system';
                card.style.padding = '0.75rem';
                card.style.marginBottom = '0.5rem';

                const isLocal = p.privacy_band === 'sovereign_native' || p.provider_id.includes('local');
                const badgeClass = isLocal ? 'mode-real' : 'mode-fallback';
                const bandLabel = isLocal ? 'LOCAL' : 'REMOTE';

                const total = p.count;
                const succ = ((p.outcomes.success / total) * 100).toFixed(0);
                const partial = ((p.outcomes.partial / total) * 100).toFixed(0);
                const fail = (((p.outcomes.fail + p.outcomes.timeout) / total) * 100).toFixed(0);

                const sampleWarning = total < 5 ? `<div style="font-size:9px; color:var(--error); margin-top:5px;"><i class="fas fa-exclamation-triangle"></i> PRELIMINARY EVIDENCE (N=${total})</div>` : '';

                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                        <strong>${p.provider_id}</strong>
                        <span class="badge ${badgeClass}" style="font-size:9px;">${bandLabel}</span>
                    </div>
                    <div style="font-size:11px; display:grid; grid-template-columns: 1fr 1fr; gap: 5px;">
                        <span>Avg Latency: <strong>${Math.round(p.avg_latency)}ms</strong></span>
                        <span>Quality: <strong>${(p.avg_quality * 100).toFixed(0)}%</strong></span>
                    </div>
                    <div style="height:4px; display:flex; margin-top:8px; border-radius:2px; overflow:hidden; background:#333;">
                        <div style="width:${succ}%; background:var(--success);"></div>
                        <div style="width:${partial}%; background:#f59e0b;"></div>
                        <div style="width:${fail}%; background:var(--error);"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:9px; margin-top:4px; opacity:0.7;">
                        <span>Success: ${succ}%</span>
                        <span>Fallback: ${partial}%</span>
                        <span>Fail: ${fail}%</span>
                    </div>
                    ${sampleWarning}
                `;
                capGroup.appendChild(card);
            });
            this.elements.forgeContent.appendChild(capGroup);
        });
    }
};

// V1.9 Governance Toggles
ui.elements.toggleGovBtn.addEventListener('click', async () => {
    const isHidden = ui.elements.govPanel.style.display === 'none';
    ui.elements.govPanel.style.display = isHidden ? 'block' : 'none';
    ui.elements.toggleGovBtn.querySelector('.fa-chevron-down').style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0)';

    if (isHidden) {
        const data = await api.getAudit().catch(() => ({ purges: [] }));
        ui.updateAudit(data.purges);
    }
});

ui.elements.refreshAuditBtn.addEventListener('click', async () => {
    const data = await api.getAudit().catch(() => ({ purges: [] }));
    ui.updateAudit(data.purges);
    ui.addLog('Auditoría actualizada.', 'system');
});

ui.elements.toggleForgeBtn.addEventListener('click', async () => {
    const isHidden = ui.elements.forgePanel.style.display === 'none';
    ui.elements.forgePanel.style.display = isHidden ? 'block' : 'none';
    ui.elements.toggleForgeBtn.querySelector('.fa-chevron-down').style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0)';

    if (isHidden) {
        try {
            ui.elements.forgeContent.innerHTML = '<div class="log-entry info"><i class="fas fa-spinner fa-spin"></i> Consulting Comparison Ledger...</div>';
            const [stats, recs, requests, affs, syncs, debt, drift] = await Promise.all([
                api.getForgeStats(),
                api.getForgeRecommendations(ui.currentLens),
                api.listSwapRequests(),
                api.getForgeAffinities(),
                api.getForgeSynergies(),
                api.getForgeStructuralDebt(),
                api.getForgeStrategicDrift()
            ]);
            ui.updateForgeHUD(stats, recs, requests, affs, syncs, debt, drift);
        } catch (e) {
            ui.elements.forgeContent.innerHTML = '<div class="log-entry error">Forge Offline or Preliminary.</div>';
            console.error('Forge Toggle Error:', e);
        }
    }
});

ui.elements.exportBtn.addEventListener('click', async () => {
    if (!ui.currentJobId) return;
    ui.addLog('Preparando exportación de verdad histórica...', 'system');
    try {
        const data = await api.getArchive(ui.currentJobId);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lingua_archive_${ui.currentJobId}.json`;
        a.click();
        ui.addLog('Archivo de gobernanza exportado con éxito.', 'success');
    } catch (e) {
        ui.addLog(`Error al exportar: ${e.message}`, 'error');
    }
});

// Block 81 HUD Actions (Delegated)
ui.elements.forgeContent.addEventListener('click', async (e) => {
    const lensBtn = e.target.closest('.lens-filter-btn');
    if (lensBtn) {
        ui.currentLens = lensBtn.dataset.lens;
        try {
            ui.elements.forgeContent.style.opacity = '0.7';
            const [stats, recs, requests, affs, syncs, debt, drift] = await Promise.all([
                api.getForgeStats(),
                api.getForgeRecommendations(ui.currentLens),
                api.listSwapRequests(),
                api.getForgeAffinities(),
                api.getForgeSynergies(),
                api.getForgeStructuralDebt(),
                api.getForgeStrategicDrift()
            ]);
            ui.updateForgeHUD(stats, recs, requests, affs, syncs, debt, drift);
            ui.elements.forgeContent.style.opacity = '1';
            ui.addLog(`Forge lens switched to: ${ui.currentLens.toUpperCase()}`, 'system');
        } catch (err) {
            console.error('Lens refresh error:', err);
        }
        return;
    }

    const requestBtn = e.target.closest('.request-swap-btn');
    const applyBtn = e.target.closest('.apply-swap-btn');

    if (requestBtn) {
        const data = {
            capability: requestBtn.dataset.cap,
            from_provider: "DEFAULT", // Logic could resolve actual current from data
            to_provider: requestBtn.dataset.to,
            rationale: requestBtn.dataset.rat,
            tradeoff: requestBtn.dataset.trade,
            strength: requestBtn.dataset.strength,
            context: "creator_manual_override"
        };
        try {
            await api.createSwapRequest(data);
            ui.addLog(`Swap request staged for ${data.capability}. Review in Forge HUD.`, 'system');
            // Refresh
            ui.elements.toggleForgeBtn.click(); ui.elements.toggleForgeBtn.click();
        } catch (err) {
            ui.addLog(`Failed to stage request: ${err.message}`, 'error');
        }
    }

    if (applyBtn) {
        const id = applyBtn.dataset.id;
        try {
            await api.applySwapRequest(id);
            ui.addLog(`Strategic Directive Applied (ID: ${id}). Provider updated.`, 'success');
            // Refresh
            ui.elements.toggleForgeBtn.click(); ui.elements.toggleForgeBtn.click();
        } catch (err) {
            ui.addLog(`Failed to apply swap: ${err.message}`, 'error');
        }
    }

    if (e.target.closest('.replay-swap-btn')) {
        const id = e.target.closest('.replay-swap-btn').dataset.id;
        try {
            const res = await api.getSwapReplay(id);
            if (res.status === 'success' && res.outcome) {
                const o = res.outcome;
                if (o.verdict === 'INSUFFICIENT_DATA') {
                    ui.addLog(`ID ${id} Replay: Insufficient data for autopsy.`, 'info');
                } else if (o.status === 'error') {
                    ui.addLog(`ID ${id} Replay Error: ${o.reason}`, 'error');
                } else {
                    const deltaText = `Lat: ${o.stats.deltas.lat_pct}%, Qual: ${o.stats.deltas.qual}`;
                    const logClass = o.verdict === 'IMPROVED' ? 'success' : (o.verdict === 'DEGRADED' ? 'error' : 'warning');
                    ui.addLog(`[AUTOPSY ID:${id}] Verdict: ${o.verdict} | ${deltaText}`, logClass);
                }
            }
        } catch (err) {
            ui.addLog(`Failed to analyze outcome: ${err.message}`, 'error');
        }
    }
});
ui.elements.clearLogsBtn.addEventListener('click', () => {
    ui.elements.logContent.innerHTML = '';
    ui.addLog('Log cleared.', 'system');
});

// Drag and Drop Logic
ui.elements.dropZone.addEventListener('click', () => ui.elements.fileInput.click());

ui.elements.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    ui.elements.dropZone.classList.add('active');
});

ui.elements.dropZone.addEventListener('dragleave', () => {
    ui.elements.dropZone.classList.remove('active');
});

ui.elements.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    ui.elements.dropZone.classList.remove('active');
    if (e.dataTransfer.files.length) {
        ui.elements.fileInput.files = e.dataTransfer.files;
        updateFileLabel();
        ui.addLog(`File dropped: ${e.dataTransfer.files[0].name}`, 'info');
    }
});

ui.elements.fileInput.addEventListener('change', () => {
    updateFileLabel();
    if (ui.elements.fileInput.files.length) {
        ui.addLog(`File selected: ${ui.elements.fileInput.files[0].name}`, 'info');
    }
});

function updateFileLabel() {
    if (ui.elements.fileInput.files.length) {
        ui.elements.fileName.textContent = `Selected: ${ui.elements.fileInput.files[0].name}`;
        ui.elements.fileName.style.display = 'block';
    }
}
