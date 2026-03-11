import { navigation } from '/core/navigation/nav-system.js';
import { stateManager } from '/core/state/state-manager.js';

// ---- Config & Initialization ----
const CHIP_ID = 'idiomas-ia';

let state = {
    sourceLang: 'auto',
    targetLang: 'en',
    lastInput: '',
    lastResult: null // { translation, transliteration, pronunciation, originalTitle }
};

// ---- Mocks & Local Datasets ----
// In the future, this will be handled by FastAPI + LLMs.
const eduMocks = {
    "hola": {
        en: {
            t: "Hello",
            tr: "he-lo",
            pr: "/helóu/"
        },
        ja: {
            t: "こんにちは",
            tr: "kon-ni-chi-wa",
            pr: "/koníchiwa/"
        }
    },
    "buenos dias": {
        en: {
            t: "Good morning",
            tr: "gud mor-ning",
            pr: "/gud mórning/"
        },
        ja: {
            t: "おはようございます",
            tr: "o-ha-yo-u-go-za-i-ma-su",
            pr: "/ohayóu gozáimas/"
        }
    },
    // Adding some base defaults for 'hello' in english -> spanish
    "hello": {
        es: {
            t: "Hola",
            tr: "o-la",
            pr: "/óla/"
        },
        ja: {
            t: "こんにちは",
            tr: "kon-ni-chi-wa",
            pr: "/koníchiwa/"
        }
    }
};

// ---- DOM Elements ----
const btnBack = document.getElementById('btn-back');
const btnTranslate = document.getElementById('btn-translate');
const btnSwapLang = document.getElementById('btn-swap-lang');

const selSource = document.getElementById('source-lang');
const selTarget = document.getElementById('target-lang');
const textInput = document.getElementById('text-input');

const outputContainer = document.getElementById('output-container');
const outTranslation = document.getElementById('out-translation');
const outTransliteration = document.getElementById('out-transliteration');
const outPronunciation = document.getElementById('out-pronunciation');
const outOriginal = document.getElementById('out-original');
const labelTraduccion = document.getElementById('label-traduccion');

// ---- Initialization ----
function init() {
    navigation.navigateTo(CHIP_ID);

    // Restore state
    const savedState = stateManager.restoreState(CHIP_ID);
    if (savedState) {
        state.sourceLang = savedState.sourceLang || 'auto';
        state.targetLang = savedState.targetLang || 'en';
        state.lastInput = savedState.lastInput || '';
        state.lastResult = savedState.lastResult || null;
    }

    // Bind to UI
    selSource.value = state.sourceLang;
    selTarget.value = state.targetLang;
    textInput.value = state.lastInput;

    if (state.lastResult) {
        renderOutput(state.lastResult, state.lastInput);
    }

    setupEventListeners();
}

// ---- Logic & Actions ----
function simulateTranslation(text, source, target) {
    // 1. Clean input
    const cleanText = text.trim().toLowerCase();

    // 2. Check mocks
    let resultObj = null;

    // Exact match in our mock DB
    if (eduMocks[cleanText] && eduMocks[cleanText][target]) {
        resultObj = eduMocks[cleanText][target];
    } else {
        // Fallback generic response to show structure without failing
        resultObj = {
            t: `[${target.toUpperCase()}] ${text}`, // Fake translation
            tr: text.split(' ').join('-') + "-[syl]", // Fake syllables
            pr: `/${cleanText.toLowerCase()}/` // Fake pronunciation
        };
    }

    return resultObj;
}

function handleTranslation() {
    const text = textInput.value;
    if (!text.trim()) return;

    const source = selSource.value;
    const target = selTarget.value;

    // Simulate backend call (sync for now)
    const result = simulateTranslation(text, source, target);

    // Update State
    state.sourceLang = source;
    state.targetLang = target;
    state.lastInput = text.trim();
    state.lastResult = {
        translation: result.t,
        transliteration: result.tr,
        pronunciation: result.pr,
        targetName: selTarget.options[selTarget.selectedIndex].text
    };

    stateManager.saveState(CHIP_ID, state);

    // Render
    renderOutput(state.lastResult, state.lastInput);
}

// ---- UI Rendering ----
function renderOutput(result, originalText) {
    // Update labels
    labelTraduccion.innerText = `Traducción al ${result.targetName}`;

    // Update contents
    outTranslation.innerText = result.translation;
    outTransliteration.innerText = result.transliteration;
    outPronunciation.innerText = result.pronunciation;
    outOriginal.innerText = originalText;

    // Show container
    outputContainer.classList.remove('hidden');
}

function handleSwap() {
    // Cannot easily swap if "auto" is selected, fallback to 'es' if so.
    let currentSource = selSource.value;
    let currentTarget = selTarget.value;

    if (currentSource === 'auto') {
        currentSource = 'es'; // default fallback
    }

    // Set UI
    selSource.value = currentTarget;
    selTarget.value = currentSource;

    // Trigger translation again if text exists
    if (textInput.value.trim().length > 0) {
        handleTranslation();
    }
}

// ---- Event Listeners ----
function setupEventListeners() {
    btnBack.addEventListener('click', () => {
        window.location.href = '/';
    });

    btnTranslate.addEventListener('click', handleTranslation);

    btnSwapLang.addEventListener('click', handleSwap);

    // Also trigger translation on Enter (if not shifting)
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleTranslation();
        }
    });

    // Save state on select change (even without translating)
    selSource.addEventListener('change', () => {
        state.sourceLang = selSource.value;
        stateManager.saveState(CHIP_ID, state);
    });

    selTarget.addEventListener('change', () => {
        state.targetLang = selTarget.value;
        stateManager.saveState(CHIP_ID, state);
    });
}

// Boot
document.addEventListener('DOMContentLoaded', init);
