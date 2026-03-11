import { navigation } from '/core/navigation/nav-system.js';
import { stateManager } from '/core/state/state-manager.js';

// ---- Config & Initialization ----
const CHIP_ID = 'finanzas';

// Initial dummy state if empty
const defaultTransactions = [
    { id: 1, type: 'income', amount: 1500.00, desc: 'Salario', date: new Date().toISOString() },
    { id: 2, type: 'expense', amount: 45.50, desc: 'Supermercado', date: new Date().toISOString() },
    { id: 3, type: 'expense', amount: 15.00, desc: 'Suscripción', date: new Date(Date.now() - 86400000).toISOString() }
];

let state = {
    transactions: [],
    balance: 0,
    income: 0,
    expense: 0,
    saving: 0
};

// ---- DOM Elements ----
const btnBack = document.getElementById('btn-back');

// Views
const viewDashboard = document.getElementById('view-dashboard');
const viewAddForm = document.getElementById('view-add-form');

// Summary elements
const summaryBalance = document.getElementById('summary-balance');
const summaryIncome = document.getElementById('summary-income');
const summaryExpense = document.getElementById('summary-expense');
const summarySaving = document.getElementById('summary-saving');
const transactionsListEl = document.getElementById('transactions-list');

// Buttons
const btnAddTransaction = document.getElementById('btn-add-transaction');
const btnSaveTransaction = document.getElementById('btn-save-transaction');
const btnCancelTransaction = document.getElementById('btn-cancel-transaction');
const typeBtns = document.querySelectorAll('.type-btn');

// Form inputs
const inputAmount = document.getElementById('input-amount');
const inputDesc = document.getElementById('input-desc');

// Local Form State
let currentSelectedType = 'expense';

// ---- Initialization ----
function init() {
    // Notify nav system
    navigation.navigateTo(CHIP_ID);

    // Try to restore previous state, otherwise use default
    const savedState = stateManager.restoreState(CHIP_ID);
    if (savedState && savedState.transactions) {
        state.transactions = savedState.transactions;
    } else {
        state.transactions = [...defaultTransactions];
    }

    calculateSummary();
    renderDashboard();
    setupEventListeners();
}

// ---- Data & State Logic ----
function calculateSummary() {
    state.income = 0;
    state.expense = 0;
    state.saving = 0;

    state.transactions.forEach(t => {
        if (t.type === 'income') state.income += t.amount;
        if (t.type === 'expense') state.expense += t.amount;
        if (t.type === 'saving') state.saving += t.amount;
    });

    state.balance = state.income - state.expense - state.saving;

    // Save state
    stateManager.saveState(CHIP_ID, state);
}

function addTransaction(type, amount, desc) {
    const newTx = {
        id: Date.now(),
        type,
        amount: parseFloat(amount),
        desc,
        date: new Date().toISOString()
    };

    // Add to beginning of array
    state.transactions.unshift(newTx);

    calculateSummary();
    renderDashboard();
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(isoString) {
    const d = new Date(isoString);
    return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

// ---- Rendering & UI logic ----
function renderDashboard() {
    // Update summary UI
    summaryBalance.innerText = formatCurrency(state.balance);
    summaryIncome.innerText = '+' + formatCurrency(state.income);
    summaryExpense.innerText = '-' + formatCurrency(state.expense);
    summarySaving.innerText = formatCurrency(state.saving);

    // Clear list
    transactionsListEl.innerHTML = '';

    if (state.transactions.length === 0) {
        transactionsListEl.innerHTML = '<li class="transaction-item" style="justify-content:center; color:var(--text-muted)">Sin movimientos</li>';
        return;
    }

    // Render transactions
    state.transactions.forEach(tx => {
        const li = document.createElement('li');
        li.className = 'transaction-item';

        let amountClass = '';
        let prefix = '';
        if (tx.type === 'income') {
            amountClass = 'amount-income';
            prefix = '+';
        } else if (tx.type === 'expense') {
            amountClass = 'amount-expense';
            prefix = '-';
        } else if (tx.type === 'saving') {
            amountClass = 'amount-saving';
            prefix = '';
        }

        li.innerHTML = `
            <div class="transaction-info">
                <span class="transaction-desc">${tx.desc}</span>
                <span class="transaction-date">${formatDate(tx.date)}</span>
            </div>
            <div class="transaction-amount ${amountClass}">
                ${prefix}${formatCurrency(tx.amount)}
            </div>
        `;

        transactionsListEl.appendChild(li);
    });
}

// ---- View Navigation ----
function showAddForm() {
    viewDashboard.classList.remove('active');
    viewDashboard.classList.add('hidden');
    viewAddForm.classList.remove('hidden');
    viewAddForm.classList.add('active');

    // reset form
    inputAmount.value = '';
    inputDesc.value = '';

    // hide FAB
    btnAddTransaction.style.display = 'none';
}

function hideAddForm() {
    viewAddForm.classList.remove('active');
    viewAddForm.classList.add('hidden');
    viewDashboard.classList.remove('hidden');
    viewDashboard.classList.add('active');

    // show FAB
    btnAddTransaction.style.display = 'flex';
}

// ---- Event Listeners ----
function setupEventListeners() {
    // Top-bar navigation
    btnBack.addEventListener('click', () => {
        window.location.href = '/';
    });

    // Sub-view navigation
    btnAddTransaction.addEventListener('click', showAddForm);
    btnCancelTransaction.addEventListener('click', hideAddForm);

    // Form logic
    typeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Remove active from all
            typeBtns.forEach(b => b.classList.remove('active'));
            // Set active to clicked
            e.target.classList.add('active');
            currentSelectedType = e.target.getAttribute('data-type');
        });
    });

    btnSaveTransaction.addEventListener('click', () => {
        const amount = inputAmount.value;
        const desc = inputDesc.value;

        if (!amount || isNaN(amount) || amount <= 0 || !desc.trim()) {
            alert("Por favor, ingresa un monto válido y una descripción.");
            return;
        }

        addTransaction(currentSelectedType, amount, desc.trim());
        hideAddForm();
    });
}

// Boot
document.addEventListener('DOMContentLoaded', init);
