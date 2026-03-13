/**
 * OmniWeb Galaxy Map (Phase 11 & 12)
 * Visualizes the system ecosystem as an interactive orbital graph with dependency flows.
 */
class GalaxyMap {
    constructor() {
        this.svg = null;
        this.viewport = null;
        this.container = null;
        this.detailOverlay = null;

        this.centerX = 500;
        this.centerY = 500;
        this.scale = 0.8;
        this.panX = 0;
        this.panY = 0;

        this.initialized = false;
        this.selectedNodeId = null;
    }

    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.container.innerHTML = `
            <svg id="galaxy-svg" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid meet">
                <defs>
                    <radialGradient id="core-glow" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stop-color="#00d4ff" stop-opacity="0.4" />
                        <stop offset="100%" stop-color="#00d4ff" stop-opacity="0" />
                    </radialGradient>
                    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
                    </marker>
                </defs>
                <g id="galaxy-viewport"></g>
            </svg>
            <div id="galaxy-detail" class="galaxy-detail-overlay"></div>
        `;

        this.svg = document.getElementById('galaxy-svg');
        this.viewport = document.getElementById('galaxy-viewport');
        this.detailOverlay = document.getElementById('galaxy-detail');

        // Initial center
        this.panX = (this.container.clientWidth / 2) - (500 * this.scale);
        this.panY = (this.container.clientHeight / 2) - (500 * this.scale);

        this.setupInteractions();
        this.updateTransform();
        this.initialized = true;
        console.log("Galaxy Map with Flows Initialized.");
    }

    setupInteractions() {
        let isDragging = false;
        let lastX, lastY;

        this.svg.onmousedown = (e) => {
            if (e.target.closest('.galaxy-node')) return; // Let node click handle it
            isDragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
        };

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = (e.clientX - lastX) * (1000 / this.container.clientWidth);
            const dy = (e.clientY - lastY) * (1000 / this.container.clientHeight);
            this.panX += dx;
            this.panY += dy;
            this.updateTransform();
            lastX = e.clientX;
            lastY = e.clientY;
        });

        window.addEventListener('mouseup', () => isDragging = false);

        this.svg.onwheel = (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.scale = Math.min(Math.max(this.scale * delta, 0.3), 3);
            this.updateTransform();
        };

        // Touch support
        this.svg.ontouchstart = (e) => {
            if (e.touches.length === 1) {
                if (e.target.closest('.galaxy-node')) return;
                isDragging = true;
                lastX = e.touches[0].clientX;
                lastY = e.touches[0].clientY;
            }
        };

        this.svg.ontouchmove = (e) => {
            if (!isDragging || e.touches.length !== 1) return;
            const dx = (e.touches[0].clientX - lastX) * (1000 / this.container.clientWidth);
            const dy = (e.touches[0].clientY - lastY) * (1000 / this.container.clientHeight);
            this.panX += dx;
            this.panY += dy;
            this.updateTransform();
            lastX = e.touches[0].clientX;
            lastY = e.touches[0].clientY;
        };

        this.svg.ontouchend = () => isDragging = false;
    }

    updateTransform() {
        if (!this.viewport) return;
        const tx = this.panX;
        const ty = this.panY;
        this.viewport.setAttribute('transform', `translate(${tx}, ${ty}) scale(${this.scale})`);
        this.viewport.style.transform = `translate(${tx}px, ${ty}px) scale(${this.scale})`;
        this.viewport.style.transformOrigin = '500px 500px';
    }

    update(state) {
        if (!this.container || !document.contains(this.container)) {
            this.initialized = false;
            this.init('galaxy-map-mount');
        }

        if (!this.initialized) return;

        // Performance Optimization: Only render if cockpit is viewing the map
        const cockpit = document.getElementById('mission-control-view');
        if (!cockpit || !cockpit.classList.contains('active')) return;

        const activeTab = document.querySelector('.cockpit-tab.active');
        if (!activeTab || activeTab.dataset.tab !== 'map') return;

        const coreNodes = [
            { id: 'auditor', name: 'System Auditor', health: state.health, icon: '🛡️', orbit: 200, angle: 0 },
            { id: 'fixer', name: 'Auto Fix', health: state.is_healing ? 'healing' : 'healthy', icon: '🔧', orbit: 200, angle: 72 },
            { id: 'logbook', name: 'Logbook', health: 'healthy', icon: '📖', orbit: 200, angle: 144 },
            { id: 'code', name: 'Code Control', health: 'healthy', icon: '💻', orbit: 200, angle: 216 },
            { id: 'aihost', name: 'AI Host', health: state.ai_host.status === 'online' ? 'healthy' : 'error', icon: '🧠', orbit: 200, angle: 288 }
        ];

        const chips = state.chips || [];
        const chipNodes = chips.map((c, i) => ({
            id: c.slug,
            name: c.name,
            health: c.health,
            status: c.status,
            icon: '🧩',
            orbit: 380,
            angle: (360 / Math.max(chips.length, 1)) * i,
            data: c
        }));

        const allNodes = [...coreNodes, ...chipNodes];
        this.renderGraph(allNodes, state);
    }

    renderGraph(nodes, state) {
        const nodePositions = {
            'core': { x: this.centerX, y: this.centerY, name: 'Omni Core' }
        };

        // Calculate positions
        nodes.forEach(n => {
            const rad = (n.angle - 90) * (Math.PI / 180);
            const x = this.centerX + n.orbit * Math.cos(rad);
            const y = this.centerY + n.orbit * Math.sin(rad);
            nodePositions[n.id] = { ...n, x, y };
        });

        let content = '';

        // 1. Draw Orbits
        [200, 380].forEach(r => {
            content += `<circle cx="${this.centerX}" cy="${this.centerY}" r="${r}" class="node-orbit" />`;
        });

        // 2. Draw Flows (Dependency Connections)
        content += this.renderFlows(nodePositions, state);

        // 3. Draw Central AI Orb GLOW
        content += `<circle cx="${this.centerX}" cy="${this.centerY}" r="120" fill="url(#core-glow)" />`;

        // 4. Render Nodes
        content += this.getNodeHTML({
            id: 'core',
            name: 'Omni Core',
            icon: '💠',
            health: state.health,
            x: this.centerX,
            y: this.centerY,
            isCore: true
        });

        nodes.forEach(n => {
            content += this.getNodeHTML(nodePositions[n.id]);
        });

        this.viewport.innerHTML = content;

        // 5. Setup Interactions
        this.viewport.querySelectorAll('.galaxy-node').forEach(el => {
            el.onclick = (e) => {
                e.stopPropagation();
                const id = el.dataset.id;
                this.selectedNodeId = (this.selectedNodeId === id) ? null : id;
                const nodeData = id === 'core' ? { id: 'core', name: 'Omni Core', health: state.health, icon: '💠' } : nodes.find(n => n.id === id);
                if (nodeData) this.showDetail(nodeData);
                this.update(state); // Refresh highlights
            };
        });
    }

    renderFlows(nodePositions, state) {
        const flows = state.flow_data || {};
        let flowContent = '';

        // Define architectural connections
        const connections = [
            { from: 'aihost', to: 'chips', id: 'ai_to_chips' },
            { from: 'auditor', to: 'fixer', id: 'auditor_to_fixer' },
            { from: 'fixer', to: 'chips', id: 'fixer_to_chips' },
            { from: 'aihost', to: 'logbook', id: 'ai_to_logbook' },
            { from: 'chips', to: 'core', id: 'chips_to_state' }
        ];

        connections.forEach(conn => {
            const flow = flows[conn.id] || { health: 'healthy', latency: 0, active: false };

            // Handle multiple targets (e.g. chips)
            let targets = [];
            if (conn.to === 'chips') {
                targets = Object.values(nodePositions).filter(p => p.orbit === 380);
            } else {
                targets = [nodePositions[conn.to]];
            }

            let source = nodePositions[conn.from];
            if (conn.from === 'chips') {
                // For chips to core, we draw from each chip
                const chipNodes = Object.values(nodePositions).filter(p => p.orbit === 380);
                chipNodes.forEach(chip => {
                    flowContent += this.getPathHTML(chip, nodePositions['core'], flow, conn.id);
                });
            } else if (source) {
                targets.forEach(target => {
                    if (target) flowContent += this.getPathHTML(source, target, flow, conn.id);
                });
            }
        });

        return flowContent;
    }

    getPathHTML(from, to, flow, flowId) {
        // Calculate path with a slight curve
        const midX = (from.x + to.x) / 2 + (to.y - from.y) * 0.1;
        const midY = (from.y + to.y) / 2 + (from.x - to.x) * 0.1;

        const pathId = `path_${from.id}_${to.id}`;
        const activeClass = (this.selectedNodeId === from.id || this.selectedNodeId === to.id) ? 'active' : '';
        const healthClass = flow.health;

        // Latency determines animation speed
        const duration = Math.max(1, (flow.latency || 20) / 10);

        return `
            <g class="galaxy-flow-group" data-flow="${flowId}">
                <path d="M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}" 
                      class="galaxy-flow-path ${healthClass} ${activeClass}" 
                      id="${pathId}" />
                <path d="M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}" 
                      class="galaxy-flow-path flow-particle ${healthClass} ${activeClass}" 
                      style="animation-duration: ${duration}s" />
                ${activeClass ? `<text class="flow-latency-label" x="${midX}" y="${midY - 10}">${flow.latency}ms</text>` : ''}
            </g>
        `;
    }

    getNodeHTML(n) {
        const r = n.isCore ? 45 : 28;
        const ringR = n.isCore ? 55 : 36;
        const fontSize = n.isCore ? 32 : 18;
        const labelY = n.isCore ? 75 : 50;
        const isSelected = this.selectedNodeId === n.id ? 'selected' : '';

        return `
            <g class="galaxy-node ${n.health} ${isSelected}" transform="translate(${n.x}, ${n.y})" data-id="${n.id}">
                <circle r="${ringR}" class="node-status-ring" stroke="currentColor" />
                <circle r="${r}" fill="rgba(10, 12, 20, 0.85)" stroke="currentColor" stroke-width="2" />
                <text y="${fontSize / 3}" font-size="${fontSize}" text-anchor="middle" pointer-events="none">${n.icon}</text>
                <text y="${labelY}" class="node-label">${n.name}</text>
            </g>
        `;
    }

    showDetail(n) {
        this.detailOverlay.classList.add('active');
        const color = n.health === 'healthy' ? '#00ff88' : (n.health === 'warning' ? '#ffcc00' : (n.health === 'healing' ? '#00d4ff' : '#ff4444'));

        let extra = '';
        if (n.data) {
            extra = `
             <p><strong>Slug:</strong> ${n.data.slug}</p>
             <p><strong>State:</strong> ${n.data.status}</p>
             <p><strong>Last Act:</strong> ${n.data.last_execution || 'never'}</p>
           `;
        }

        this.detailOverlay.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <h3>${n.name}</h3>
                <button onclick="this.parentElement.parentElement.classList.remove('active')" style="background:none; border:none; color:#888; cursor:pointer; font-size:16px;">×</button>
            </div>
            <p><strong>Status:</strong> ${n.health.toUpperCase()}</p>
            ${extra}
            <div class="status-tag" style="background: ${color}; color: #000">${n.health}</div>
        `;
    }
}

window.galaxyMap = new GalaxyMap();
