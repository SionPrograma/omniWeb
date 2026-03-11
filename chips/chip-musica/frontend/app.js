/**
 * OmniWeb Music Chip - Mini App
 * Scale & Chord Explorer
 */

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

const SCALES = {
    major: [0, 2, 4, 5, 7, 9, 11],
    dorian: [0, 2, 3, 5, 7, 9, 10],
    phrygian: [0, 1, 3, 5, 7, 8, 10],
    lydian: [0, 2, 4, 6, 7, 9, 11],
    mixolydian: [0, 2, 4, 5, 7, 9, 10],
    minor: [0, 2, 3, 5, 7, 8, 10],
    locrian: [0, 1, 3, 5, 6, 8, 10],
    pentatonic: [0, 2, 4, 7, 9]
};

const CHORD_STEPS = {
    major: ['Major', 'minor', 'minor', 'Major', 'Major', 'minor', 'diminished'],
    minor: ['minor', 'diminished', 'Major', 'minor', 'minor', 'Major', 'Major']
};

class MusicExplorer {
    constructor() {
        this.rootEl = document.getElementById('root-note');
        this.scaleEl = document.getElementById('scale-type');
        this.displayEl = document.getElementById('scale-display');
        this.chordsEl = document.getElementById('chords-grid');

        this.init();
    }

    init() {
        this.rootEl.addEventListener('change', () => this.update());
        this.scaleEl.addEventListener('change', () => this.update());

        this.update();
        this.createStars();
    }

    update() {
        const root = this.rootEl.value;
        const scaleType = this.scaleEl.value;

        const scaleNotes = this.getScaleNotes(root, scaleType);
        this.renderScale(scaleNotes);
        this.renderChords(scaleNotes, scaleType);
    }

    getScaleNotes(root, type) {
        const rootIdx = NOTES.indexOf(root);
        const intervals = SCALES[type] || SCALES.major;

        return intervals.map(interval => {
            const idx = (rootIdx + interval) % 12;
            return NOTES[idx];
        });
    }

    renderScale(notes) {
        this.displayEl.innerHTML = '';
        notes.forEach((note, idx) => {
            const bubble = document.createElement('div');
            bubble.className = `note-bubble ${idx === 0 ? 'tonic' : ''}`;
            bubble.innerText = note;
            this.displayEl.appendChild(bubble);
        });
    }

    renderChords(notes, scaleType) {
        this.chordsEl.innerHTML = '';

        // Simple logic for diatonic chords (triads)
        // Just as an example for the MVP
        const isMinor = scaleType === 'minor' || scaleType === 'dorian' || scaleType === 'phrygian' || scaleType === 'locrian';
        const template = isMinor ? CHORD_STEPS.minor : CHORD_STEPS.major;

        notes.forEach((note, idx) => {
            if (idx >= template.length) return;

            const card = document.createElement('div');
            card.className = 'chord-card';

            const name = document.createElement('span');
            name.className = 'chord-name';
            name.innerText = note;

            const type = document.createElement('span');
            type.className = 'chord-type';
            type.innerText = template[idx];

            card.appendChild(name);
            card.appendChild(type);
            this.chordsEl.appendChild(card);
        });
    }

    createStars() {
        const container = document.getElementById('stars');
        for (let i = 0; i < 50; i++) {
            const star = document.createElement('div');
            star.style.position = 'absolute';
            star.style.width = '2px';
            star.style.height = '2px';
            star.style.background = 'white';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.opacity = Math.random();
            container.appendChild(star);
        }
    }
}

// Start the app
new MusicExplorer();
