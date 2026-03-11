import { navigation } from '/core/navigation/nav-system.js';
import { stateManager } from '/core/state/state-manager.js';

// ---- Config & Initialization ----
const CHIP_ID = 'reparto';

// Default stops (fallback and initial map view)
const defaultStops = [
    { id: 1, name: "Empresa Transportes A", address: "Av. Principal 123", orderId: "RPT-001", status: "PENDIENTE", lat: 36.7213, lng: -4.4214 },
    { id: 2, name: "Almacen Norte", address: "Calle Industrial 45", orderId: "RPT-002", status: "PENDIENTE", lat: 36.7113, lng: -4.4314 },
    { id: 3, name: "Cliente VIP 1", address: "Boulevard Central 89", orderId: "RPT-003", status: "PENDIENTE", lat: 36.7313, lng: -4.4114 },
    { id: 4, name: "Despacho B", address: "Av. Costanera 101", orderId: "RPT-004", status: "PENDIENTE", lat: 36.7413, lng: -4.4014 },
];

let stops = [];
let markers = new Map(); // id -> marker
let map = null;
let currentDetailId = null;

// ---- DOM Elements ----
const btnBack = document.getElementById('btn-back');
const btnToggleDrawer = document.getElementById('btn-toggle-drawer');
const opsDrawer = document.getElementById('ops-drawer');
const viewList = document.getElementById('view-list');
const viewDetail = document.getElementById('view-detail');
const stopsListEl = document.getElementById('stops-list');
const progressText = document.getElementById('progress-text');
const progressBar = document.getElementById('progress-bar');

// Map Mode Elements
const btnMapMode = document.getElementById('btn-map-mode');
const btnLocate = document.getElementById('btn-locate');

// Detail elements
const detailAddress = document.getElementById('detail-address');
const detailName = document.getElementById('detail-name');
const detailOrderId = document.getElementById('detail-order-id');
const detailStatus = document.getElementById('detail-status');

// Detail action buttons
const btnMarkDelivered = document.getElementById('btn-mark-delivered');
const btnMarkAbsent = document.getElementById('btn-mark-absent');
const btnMarkPending = document.getElementById('btn-mark-pending');
const btnCloseDetail = document.getElementById('btn-close-detail');
const btnBackToList = document.getElementById('btn-back-to-list');

// Chat & Action Masiva
const btnWaAction = document.getElementById('btn-wa-action');
const chatInput = document.getElementById('chat-input');
const btnChatSend = document.getElementById('btn-chat-send');
const chatLog = document.getElementById('chat-log');

// ---- Initialization ----
async function init() {
    navigation.navigateTo(CHIP_ID);

    // Initial Drawer state from persistent preference? (optional)
    // opsDrawer.classList.toggle('closed', !shouldOpen);

    await loadData();
    initMap();
    renderStopsList();
    updateProgress();
    setupEventListeners();
}

async function loadData() {
    try {
        const response = await fetch('/api/v1/reparto/stops');
        if (response.ok) {
            const data = await response.json();
            stops = data.stops || [...defaultStops];
        } else {
            throw new Error('Backend not ready');
        }
    } catch (e) {
        console.warn("Backend fail, using local state:", e);
        const savedState = stateManager.restoreState(CHIP_ID);
        stops = (savedState && savedState.stops) ? savedState.stops : [...defaultStops];
    }
}

// ---- Map Logic (Referencia 2) ----
function initMap() {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;

    // Portable-First: Si Leaflet no ha cargado (CDN bloqueado), no rompemos la App
    if (typeof L === 'undefined') {
        console.warn("Leaflet library not loaded. Running in Map-less mode.");
        mapEl.innerHTML = `
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--text-muted); text-align:center; padding: 2rem;">
                <p>Mapa no disponible (offline o bloqueo de red).</p>
                <p style="font-size:0.8rem; margin-top:0.5rem;">El panel operativo sigue estando disponible.</p>
            </div>
        `;
        return;
    }

    try {
        map = L.map('map', {
            zoomControl: false, // Cleaner UI
            preferCanvas: true
        });

        const tilesGray = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CARTO'
        });
        const tilesColor = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OSM'
        });

        // Default mode: Gray (from Ref 2)
        tilesGray.addTo(map);
        map.currentMode = 'gray';

        // Focus map on stops
        if (stops.length > 0) {
            const points = stops.map(s => [s.lat || 36.72, s.lng || -4.42]);
            const bounds = L.latLngBounds(points);
            map.fitBounds(bounds.pad(0.2));
        } else {
            map.setView([36.72, -4.42], 13);
        }

        // Add Markers
        stops.forEach(createMarker);
    } catch (e) {
        console.error("Error initializing Leaflet map:", e);
        mapEl.innerHTML = `<div style="padding:2rem; text-align:center;">Error al cargar el mapa.</div>`;
    }
}

function createMarker(stop) {
    const marker = L.marker([stop.lat, stop.lng], {
        icon: createMarkerIcon(stop.status),
        title: stop.name
    }).addTo(map);

    marker.on('click', () => {
        openDetailView(stop.id);
        // Auto-open drawer if closed
        opsDrawer.classList.remove('closed');
    });

    markers.set(stop.id, marker);
}

function createMarkerIcon(status) {
    const cls = status.toLowerCase() === 'entregado' ? 'delivered' :
        (status.toLowerCase() === 'ausente' ? 'absent' : 'pending');

    return L.divIcon({
        className: `chip-marker ${cls}`,
        html: `<div class="m-dot"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
}

function updateMarkerIcon(stopId, status) {
    const marker = markers.get(stopId);
    if (marker) {
        marker.setIcon(createMarkerIcon(status));
    }
}

// ---- UI & Rendering ----
function renderStopsList() {
    stopsListEl.innerHTML = '';
    stops.forEach(stop => {
        const li = document.createElement('li');
        li.className = `stop-item ${currentDetailId === stop.id ? 'active' : ''}`;

        const statusLabel = stop.status.charAt(0).toUpperCase() + stop.status.slice(1).toLowerCase();
        const tagClass = `tag-${stop.status.toLowerCase()}`;

        li.innerHTML = `
            <div class="stop-info">
                <strong>${stop.address}</strong>
                <span>${stop.name}</span>
            </div>
            <div class="stop-status">
                <span class="badge ${tagClass}">${statusLabel}</span>
            </div>
        `;

        li.addEventListener('click', () => {
            openDetailView(stop.id);
            map.flyTo([stop.lat, stop.lng], 16, { duration: 1 });
        });
        stopsListEl.appendChild(li);
    });
}

function updateProgress() {
    const total = stops.length;
    const delivered = stops.filter(s => s.status === 'ENTREGADO').length;
    if (progressText) progressText.innerText = `${delivered}/${total}`;
    if (progressBar) progressBar.style.width = `${total > 0 ? (delivered / total) * 100 : 0}%`;
}

// ---- Navigation ----
function openDetailView(id) {
    currentDetailId = id;
    const stop = stops.find(s => s.id === id);
    if (!stop) return;

    detailAddress.innerText = stop.address;
    detailName.innerText = stop.name;
    detailOrderId.innerText = stop.orderId || `#${stop.id}`;

    updateDetailStatusUI(stop.status);

    viewList.classList.add('hidden');
    viewDetail.classList.remove('hidden');

    renderStopsList(); // Update active class
}

function closeDetailView() {
    currentDetailId = null;
    viewDetail.classList.add('hidden');
    viewList.classList.remove('hidden');
    renderStopsList();
}

function updateDetailStatusUI(status) {
    const tagClass = `tag-${status.toLowerCase()}`;
    detailStatus.className = `badge ${tagClass}`;
    detailStatus.innerText = status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
}

// ---- Actions ----
async function changeStopStatus(newStatus) {
    if (!currentDetailId) return;

    const stopIndex = stops.findIndex(s => s.id === currentDetailId);
    if (stopIndex !== -1) {
        stops[stopIndex].status = newStatus;
        updateDetailStatusUI(newStatus);
        updateMarkerIcon(currentDetailId, newStatus);
        updateProgress();
        renderStopsList();

        // Sync (Backend / Local)
        try {
            await fetch(`/api/v1/reparto/stops/${currentDetailId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
        } catch (e) {
            console.warn('Sync failed:', e);
        }
        stateManager.saveState(CHIP_ID, { stops });
    }
}

// ---- Listeners & Handlers ----
function setupEventListeners() {
    // Top Bar
    btnBack.addEventListener('click', () => window.location.href = '/');

    btnToggleDrawer.addEventListener('click', () => {
        opsDrawer.classList.toggle('closed');
        if (map) {
            setTimeout(() => map.invalidateSize(), 400); // Recalculate map on drawer transition
        }
    });

    // Map Controls
    btnMapMode?.addEventListener('click', () => {
        if (!map || typeof L === 'undefined') return;
        // Toggle tiles simplified logic
        if (map.currentMode === 'gray') {
            map.eachLayer(l => { if (l instanceof L.TileLayer) map.removeLayer(l); });
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
            map.currentMode = 'color';
            btnMapMode.innerText = 'Mapa: Color';
        } else {
            map.eachLayer(l => { if (l instanceof L.TileLayer) map.removeLayer(l); });
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);
            map.currentMode = 'gray';
            btnMapMode.innerText = 'Mapa: Gris';
        }
    });

    btnLocate?.addEventListener('click', () => {
        if (!map || typeof L === 'undefined') return;
        map.locate({ setView: true, maxZoom: 16 });
        map.on('locationfound', (e) => {
            L.circleMarker(e.latlng, { radius: 5, color: '#5271ff' }).addTo(map);
        });
    });

    // Detail Actions
    btnMarkDelivered.addEventListener('click', () => changeStopStatus('ENTREGADO'));
    btnMarkAbsent.addEventListener('click', () => changeStopStatus('AUSENTE'));
    btnMarkPending.addEventListener('click', () => changeStopStatus('PENDIENTE'));
    btnCloseDetail.addEventListener('click', closeDetailView);
    btnBackToList.addEventListener('click', closeDetailView);

    // Extra: Chat & WHATSAPP
    btnChatSend?.addEventListener('click', sendChatMessage);
    chatInput?.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendChatMessage(); });
    btnWaAction?.addEventListener('click', () => {
        const start = document.getElementById('wa-start').value || '10:00';
        const end = document.getElementById('wa-end').value || '11:00';
        alert(`Simulando envío masivo por WhatsApp para el rango ${start} - ${end}`);
    });
}

function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.innerHTML = `<span style="color:#999">[${time}]</span> <b>Yo:</b> ${text}`;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
    chatInput.value = '';
}

// Boot
document.addEventListener('DOMContentLoaded', init);
