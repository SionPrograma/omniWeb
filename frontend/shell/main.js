document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const aiHostView = document.getElementById('ai-host-view');
    const chipView = document.getElementById('active-chip-view');
    const chipFrame = document.getElementById('chip-frame');
    const chipTitle = document.getElementById('active-chip-title');
    const closeChipBtn = document.getElementById('close-chip');

    const launcherOverlay = document.getElementById('launcher-overlay');
    const openLauncherBtn = document.getElementById('open-launcher');
    const launcherItems = document.querySelectorAll('.chip-launcher-item');

    const navItems = document.querySelectorAll('.nav-item');
    const contextPanel = document.getElementById('context-panel');

    const shellInput = document.getElementById('shell-input');
    const sendBtn = document.getElementById('send-command');
    const chatLog = document.getElementById('chat-log');

    // --- State ---
    let activeView = 'chat';

    // --- Launcher Logic ---
    openLauncherBtn.addEventListener('click', () => {
        launcherOverlay.classList.toggle('active');
        openLauncherBtn.classList.toggle('active');
    });

    launcherItems.forEach(item => {
        item.addEventListener('click', () => {
            if (item.classList.contains('disabled')) return;

            const url = item.getAttribute('data-url');
            const title = item.getAttribute('data-chip');
            launchChip(url, title);
            launcherOverlay.classList.remove('active');
        });
    });

    // --- Chip Management ---
    function launchChip(url, title) {
        console.log(`Launching chip: ${title} at ${url}`);
        chipTitle.innerText = `Chip: ${title.charAt(0).toUpperCase() + title.slice(1)}`;
        chipFrame.src = url;
        chipView.classList.add('active');

        // Minimize AI Host
        aiHostView.classList.remove('active');
    }

    closeChipBtn.addEventListener('click', () => {
        chipView.classList.remove('active');
        aiHostView.classList.add('active');
        setTimeout(() => {
            chipFrame.src = ''; // Clear iframe after transition
        }, 400);
    });

    // --- Navigation Logic ---
    navItems.forEach(nav => {
        nav.addEventListener('click', () => {
            const view = nav.getAttribute('data-view');
            if (!view) return;

            navItems.forEach(n => n.classList.remove('active'));
            nav.classList.add('active');

            if (view === 'context') {
                toggleContext(true);
            } else {
                toggleContext(false);
            }
        });
    });

    function toggleContext(show) {
        // Implementation for context panel sliding logic
        console.log("Context toggle:", show);
    }

    // --- Chat / Command Logic ---
    function addMessage(text, sender = 'ai') {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.innerHTML = `<div class="msg-bubble">${text}</div>`;
        chatLog.appendChild(msgDiv);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    sendBtn.addEventListener('click', processCommand);
    shellInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') processCommand();
    });

    async function processCommand() {
        const cmd = shellInput.value.trim();
        if (!cmd) return;

        addMessage(cmd, 'user');
        shellInput.value = '';

        // Typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai typing';
        typingDiv.innerHTML = '<div class="msg-bubble">...</div>';
        chatLog.appendChild(typingDiv);
        chatLog.scrollTop = chatLog.scrollHeight;

        try {
            const response = await fetch('/api/v1/ai-host/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer omniweb-dev-secret-token' // Default dev token
                },
                body: JSON.stringify({ message: cmd })
            });

            const data = await response.json();
            typingDiv.remove();

            if (data.message) {
                addMessage(data.message, 'ai');
            }

            // Visual Payload Handling (Step 6)
            if (data.payload?.visual) {
                handleVisualResponse(data.payload.visual);
            } else if (data.display_data) {
                // SuperCommand display data
                handleVisualResponse({
                    type: 'task-report',
                    title: data.display_data.task_title || 'Task Execution',
                    data: {
                        status: data.payload.status,
                        actions: data.payload.actions,
                        issues: data.payload.issues
                    }
                });
            }

            // Intent Handling
            if (data.intent === 'open_chip' && data.payload?.target) {
                const url = `/${data.payload.target}/`;
                setTimeout(() => launchChip(url, data.payload.target), 1000);
            }

            if (data.intent === 'logbook_entry_created') {
                // visual hint that it was saved
                const logBtn = document.querySelector('[onclick="masterLogbook.toggle()"]');
                if (logBtn) {
                    logBtn.style.color = '#32ff96';
                    setTimeout(() => logBtn.style.color = '', 2000);
                }
            }

        } catch (error) {
            console.error('AI Host Error:', error);
            typingDiv.remove();
            addMessage("I'm having trouble connecting to the core system. Please verify connection.", 'ai');
        }
    }

    function handleVisualResponse(visual) {
        console.log("Rendering visual response:", visual);
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ai-visual type-${visual.type}`;

        let content = `<div class="visual-card">
            <h4>${visual.title || 'System Update'}</h4>`;

        if (visual.type === 'task-report') {
            const actions = visual.data.actions || [];
            content += `<ul style="font-size: 0.8rem; margin-top: 5px; list-style: none; padding: 0;">
                ${actions.map(a => `<li style="color: #32ff96;">✓ ${a}</li>`).join('')}
            </ul>`;
            if (visual.data.issues?.length > 0) {
                content += `<p style="color: #ff5050; font-size: 0.7rem; margin-top: 5px;">! ${visual.data.issues[0]}</p>`;
            }
        } else if (visual.type === 'chip-modification-success') {
            content += `<p style="font-size: 0.8rem; color: #32ff96;">${visual.data}</p>`;
        } else {
            content += `<pre style="font-size: 0.7rem; color: var(--text-dim); overflow: auto;">${JSON.stringify(visual.data, null, 2)}</pre>`;
        }

        content += `</div>`;
        msgDiv.innerHTML = content;
        chatLog.appendChild(msgDiv);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // --- Particles Background ---
    function createParticles() {
        const container = document.getElementById('particles');
        if (!container) return;
        for (let i = 0; i < 20; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            p.style.cssText = `
                position: absolute;
                width: 2px;
                height: 2px;
                background: white;
                opacity: ${Math.random()};
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                border-radius: 50%;
                pointer-events: none;
            `;
            container.appendChild(p);
        }
    }
    createParticles();
});
