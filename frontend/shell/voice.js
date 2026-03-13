/**
 * OMNIWEB VOICE INTERFACE
 * Handles Speech-to-Text (STT) and Text-to-Speech (TTS)
 */

class VoiceInterface {
    constructor(options = {}) {
        this.recognition = null;
        this.isListening = false;
        this.synth = window.speechSynthesis;
        this.onResultCallback = options.onResult || (() => { });
        this.onStateChangeCallback = options.onStateChange || (() => { });
        this.onSpeechStartCallback = options.onSpeechStart || (() => { });
        this.onSpeechEndCallback = options.onSpeechEnd || (() => { });

        this.initRecognition();
    }

    initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition API not supported in this browser.");
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = document.documentElement.lang || navigator.language || 'en-US';

        this.recognition.onstart = () => {
            this.isListening = true;
            this.onStateChangeCallback(true);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.onStateChangeCallback(false);
        };

        this.recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            this.isListening = false;
            this.onStateChangeCallback(false);

            if (event.error === 'not-allowed') {
                alert("Microphone access denied. Please enable it in your browser settings.");
            }
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.onResultCallback(transcript);
        };
    }

    toggle() {
        if (!this.recognition) {
            alert("Speech recognition is not supported in this browser.");
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
            } catch (err) {
                console.error("Failed to start recognition:", err);
            }
        }
    }

    speak(text) {
        if (!this.synth) return;

        // Cancel any ongoing speech
        this.synth.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = document.documentElement.lang || navigator.language || 'en-US';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Find a nice voice if possible
        const voices = this.synth.getVoices();
        // Priority: Natural sounding voices in the target language
        const preferredVoice = voices.find(v => v.lang.startsWith(utterance.lang) && (v.name.includes('Google') || v.name.includes('Natural')))
            || voices.find(v => v.lang.startsWith(utterance.lang))
            || voices[0];

        if (preferredVoice) utterance.voice = preferredVoice;

        utterance.onstart = () => this.onSpeechStartCallback();
        utterance.onend = () => this.onSpeechEndCallback();
        utterance.onerror = () => this.onSpeechEndCallback();

        this.synth.speak(utterance);
    }
}

// Export to window for access in main.js
window.VoiceInterface = VoiceInterface;
