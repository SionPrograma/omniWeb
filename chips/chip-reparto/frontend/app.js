import { navigation } from '/core/navigation/nav-system.js';
import { stateManager } from '/core/state/state-manager.js';

// ---- Config & Initialization ----
const CHIP_ID = 'reparto';

// Mock Stops data - Initial template if no state is saved
const defaultStops = [
    { id: 1, name: "Empresa de Transportes A", address: "Av. Principal 123", orderId: "RPT-001", status: "PENDIENTE" },
    { id: 2, name: "Almacen Norte", address: "Calle Industrial 45", orderId: "RPT-002", status: "PENDIENTE" },
    { id: 3, name: "Cliente VIP 1", address: "Boulevard Central 89", orderId: "RPT-003", status: "PENDIENTE" },
    { id: 4, name: "Despacho B", address: "Av. Costanera 101", orderId: "RPT-004", status: "PENDIENTE" },
];

let stops = [];
let currentDetailId = null;

// ---- DOM Elements ----
const btnBack = document.getElementById('btn-back');
const viewList = document.getElementById('view-list');
const viewDetail = document.getElementById('view-detail');
const stopsListEl = document.getElementById('stops-list');
const progressText = document.getElementById('progress-text');
const progressBar = document.getElementById('progress-bar');

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

// ---- Initialization ----
function init() {
    navigation.navigateTo(CHIP_ID);

    // Try to restore previous state, otherwise use default
    const savedState = stateManager.restoreState(CHIP_ID);
    if (savedState && savedState.stops) {
        stops = savedState.stops;
    } else {
        stops = [...defaultStops];
    }

    renderStopsList();
    updateProgress();
    setupEventListeners();
}

// ---- Rendering & UI logic ----
function renderStopsList() {
    stopsListEl.innerHTML = '';

    stops.forEach(stop => {
        const li = document.createElement('li');
        li.className = 'stop-item';

        // Define color tag by status
        let statusClass = 'tag-pending';
        let statusText = 'Pendiente';
        if (stop.status === 'ENTREGADO') { statusClass = 'tag-delivered'; statusText = 'Entregado'; }
        if (stop.status === 'AUSENTE') { statusClass = 'tag-absent'; statusText = 'Ausente'; }

        li.innerHTML = `
            <div class="stop-info">
                <strong>${stop.address}</strong>
                <span>${stop.name}</span>
            </div>
            <div class="stop-status">
                <span class="status-tag ${statusClass}">${statusText}</span>
            </div>
        `;

        li.addEventListener('click', () => openDetailView(stop.id));
        stopsListEl.appendChild(li);
    });
}

function updateProgress() {
    const total = stops.length;
    const delivered = stops.filter(s => s.status === 'ENTREGADO').length;

    progressText.innerText = `${delivered}/${total}`;
    const percentage = total > 0 ? (delivered / total) * 100 : 0;
    progressBar.style.width = `${percentage}%`;
}

// ---- Navigation logic (inside chip) ----
function openDetailView(id) {
    currentDetailId = id;
    const stop = stops.find(s => s.id === id);
    if (!stop) return;

    detailAddress.innerText = stop.address;
    detailName.innerText = stop.name;
    detailOrderId.innerText = stop.orderId;

    updateDetailStatusUI(stop.status);

    // Switch view classes
    viewList.classList.remove('active');
    viewList.classList.add('hidden');
    viewDetail.classList.remove('hidden');
    viewDetail.classList.add('active');
}

function closeDetailView() {
    currentDetailId = null;
    viewDetail.classList.remove('active');
    viewDetail.classList.add('hidden');
    viewList.classList.remove('hidden');
    viewList.classList.add('active');
}

// ---- Action logic ----
function updateDetailStatusUI(status) {
    let statusClass = '';
    let statusText = '';
    if (status === 'ENTREGADO') {
        statusText = 'Entregado';
        statusClass = 'tag-delivered';
    } else if (status === 'AUSENTE') {
        statusText = 'Ausente';
        statusClass = 'tag-absent';
    } else {
        statusText = 'Pendiente';
        statusClass = 'tag-pending';
    }

    detailStatus.className = `badge ${statusClass}`;
    detailStatus.innerText = statusText;
}

function changeStopStatus(newStatus) {
    if (!currentDetailId) return;

    const stopIndex = stops.findIndex(s => s.id === currentDetailId);
    if (stopIndex !== -1) {
        stops[stopIndex].status = newStatus;
        updateDetailStatusUI(newStatus);

        // Save state logic
        stateManager.saveState(CHIP_ID, { stops });

        // Re-render hidden list
        renderStopsList();
        updateProgress();
    }
}

// ---- Event Listeners ----
function setupEventListeners() {
    // Top-bar navigation
    btnBack.addEventListener('click', () => {
        // Logica para volver al dashboard principal de OmniWeb
        window.location.href = '/';
    });

    // Sub-view navigation
    btnCloseDetail.addEventListener('click', closeDetailView);

    // Status actions
    btnMarkDelivered.addEventListener('click', () => changeStopStatus('ENTREGADO'));
    btnMarkAbsent.addEventListener('click', () => changeStopStatus('AUSENTE'));
    btnMarkPending.addEventListener('click', () => changeStopStatus('PENDIENTE'));
}

// Boot
document.addEventListener('DOMContentLoaded', init);
