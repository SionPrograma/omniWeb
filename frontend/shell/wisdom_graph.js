/* OMNIWEB — BLOQUE: WISDOM GRAPH EXPLORER (VISTA DE GRAFO DEL ATLAS DE SABIDURÍA) */

class WisdomGraphExplorer {
    constructor() {
        this.nodes = [];
        this.links = [];
        this.viewPort = null;
        this.svg = null;
        this.g = null;
        this.width = 0;
        this.height = 0;
        this.simulation = null;
        this.zoom = { k: 1, x: 0, y: 0 };
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.viewOffset = { x: 0, y: 0 };
    }

    async init() {
        this.viewPort = document.getElementById('wisdom-graph-viewport');
        if (!this.viewPort) return;

        this.width = this.viewPort.offsetWidth;
        this.height = this.viewPort.offsetHeight;

        this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        this.svg.setAttribute("id", "wisdom-graph-svg");
        this.svg.setAttribute("viewBox", `0 0 ${this.width} ${this.height}`);
        this.viewPort.appendChild(this.svg);

        this.g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        this.svg.appendChild(this.g);

        this._setupEvents();
        await this.refresh();
    }

    async refresh() {
        try {
            const response = await fetch('/api/v1/governance/wisdom/graph/data', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
            });
            const data = await response.json();
            if (data.status === 'success') {
                this.nodes = data.payload.nodes;
                this.links = data.payload.links;
                this.render();
            }
        } catch (err) {
            console.error("Failed to fetch graph data:", err);
        }
    }

    render() {
        this.g.innerHTML = '';

        // Initial layout if nodes have no pos
        this.nodes.forEach((node, i) => {
            const angle = (i / this.nodes.length) * 2 * Math.PI;
            const radius = Math.min(this.width, this.height) / 3;
            node.x = this.width / 2 + radius * Math.cos(angle);
            node.y = this.height / 2 + radius * Math.sin(angle);
            node.vx = 0;
            node.vy = 0;
        });

        // Run simple force simulation (limited steps)
        for (let i = 0; i < 100; i++) {
            this._applyForces();
        }

        this._draw();
    }

    _applyForces() {
        const k = 0.05; // Spring constant
        const repulsion = 4000;

        // 1. Repulsion
        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                const n1 = this.nodes[i];
                const n2 = this.nodes[j];
                const dx = n2.x - n1.x;
                const dy = n2.y - n1.y;
                const d2 = dx * dx + dy * dy + 0.1;
                const f = repulsion / d2;
                const fx = (dx / Math.sqrt(d2)) * f;
                const fy = (dy / Math.sqrt(d2)) * f;
                n1.vx -= fx; n1.vy -= fy;
                n2.vx += fx; n2.vy += fy;
            }
        }

        // 2. Spring (Links)
        this.links.forEach(l => {
            const s = this.nodes.find(n => n.id === l.source);
            const t = this.nodes.find(n => n.id === l.target);
            if (!s || !t) return;
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const d = Math.sqrt(dx * dx + dy * dy) + 0.1;
            const f = (d - 120) * k;
            const fx = (dx / d) * f;
            const fy = (dy / d) * f;
            s.vx += fx; s.vy += fy;
            t.vx -= fx; t.vy -= fy;
        });

        // 3. Center gravity
        this.nodes.forEach(n => {
            n.vx += (this.width / 2 - n.x) * 0.01;
            n.vy += (this.height / 2 - n.y) * 0.01;

            n.x += n.vx;
            n.y += n.vy;
            n.vx *= 0.8;
            n.vy *= 0.8;
        });
    }

    _draw() {
        this.g.innerHTML = '';

        // Links
        this.links.forEach(l => {
            const s = this.nodes.find(n => n.id === l.source);
            const t = this.nodes.find(n => n.id === l.target);
            if (!s || !t) return;

            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", s.x);
            line.setAttribute("y1", s.y);
            line.setAttribute("x2", t.x);
            line.setAttribute("y2", t.y);
            line.setAttribute("class", `graph-edge ${l.type}`);
            this.g.appendChild(line);
        });

        // Nodes
        this.nodes.forEach(n => {
            const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
            group.setAttribute("class", "graph-node");
            group.setAttribute("transform", `translate(${n.x}, ${n.y})`);
            group.onclick = () => this._onNodeClick(n);

            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("r", 15 + (n.reusability * 15));
            circle.setAttribute("class", "node-circle");
            circle.setAttribute("stroke", this._getNodeColor(n));
            group.appendChild(circle);

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.textContent = n.title.substring(0, 15) + "...";
            text.setAttribute("dy", 25 + (n.reusability * 10));
            text.setAttribute("class", "node-label");
            group.appendChild(text);

            this.g.appendChild(group);
        });
    }

    _getNodeColor(node) {
        switch (node.type) {
            case 'LEARNING': return '#4ade80';
            case 'AUTOPSY': return '#60a5fa';
            case 'DECISION': return '#fbbf24';
            case 'REPLAY_SYNC': return '#f87171';
            case 'CONTEXT_MAPPING': return '#a78bfa';
            default: return '#94a3b8';
        }
    }

    _onNodeClick(node) {
        // Open the atlas detail view
        if (window.wisdomAtlas) {
            window.wisdomAtlas.viewNodeDetail(node.id);
        }
    }

    _setupEvents() {
        this.viewPort.onmousedown = (e) => {
            this.isDragging = true;
            this.dragStart = { x: e.clientX, y: e.clientY };
        };

        window.onmousemove = (e) => {
            if (!this.isDragging) return;
            const dx = e.clientX - this.dragStart.x;
            const dy = e.clientY - this.dragStart.y;
            this.viewOffset.x += dx;
            this.viewOffset.y += dy;
            this.g.setAttribute("transform", `translate(${this.viewOffset.x}, ${this.viewOffset.y})`);
            this.dragStart = { x: e.clientX, y: e.clientY };
        };

        window.onmouseup = () => {
            this.isDragging = false;
        };

        // Resize handle
        window.onresize = () => {
            if (!this.viewPort) return;
            this.width = this.viewPort.offsetWidth;
            this.height = this.viewPort.offsetHeight;
            this.svg.setAttribute("viewBox", `0 0 ${this.width} ${this.height}`);
        };
    }

    toggle() {
        const layer = document.getElementById('wisdom-graph-layer');
        if (layer.classList.contains('active')) {
            layer.classList.remove('active');
        } else {
            layer.classList.add('active');
            this.refresh();
        }
    }
}

window.wisdomGraph = new WisdomGraphExplorer();
