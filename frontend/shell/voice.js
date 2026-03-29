/**
 * OMNIWEB VOICE INTERFACE (RECONSTRUCTED)
 * Handles Speech-to-Text (STT) and Text-to-Speech (TTS) with Mobile-First stability.
 */

class VoiceInterface {
    constructor(options = {}) {
        this.recognition = null;
        this.isListening = false;
        this.lastError = null;
        this.permissionStatus = 'unknown'; // unknown, granted, denied, unsupported
        this.synth = window.speechSynthesis;

        // Callbacks
        this.onResultCallback = options.onResult || (() => { });
        this.onStateChangeCallback = options.onStateChange || (() => { });
        this.onSpeechStartCallback = options.onSpeechStart || (() => { });
        this.onSpeechEndCallback = options.onSpeechEnd || (() => { });
        this.onErrorCallback = options.onError || (() => { });

        this.initRecognition();
    }

    async initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            this.permissionStatus = 'unsupported';
            console.error("DIAGNOSTIC: Speech Recognition API not supported.");
            return;
        }

        // Secure Context Check (Critical for mobile)
        console.log(`[VOICE_INIT] SecureContext: ${window.isSecureContext}, Host: ${window.location.hostname}`);
        if (!window.isSecureContext && window.location.hostname !== 'localhost') {
            console.warn("[VOICE_BLOCK] Secure context required for Web Speech API on this origin.");
            this.onErrorCallback('browser-unsupported');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true; // Changed to true for better mobile feedback
        this.recognition.lang = document.documentElement.lang || navigator.language || 'en-US';

        this.recognition.onstart = () => {
            console.log("VOICE: Recognition started");
            this.isListening = true;
            this.onStateChangeCallback('listening');
        };

        this.recognition.onend = () => {
            console.log("VOICE: Recognition ended");
            this.isListening = false;
            this.onStateChangeCallback('idle');
        };

        this.recognition.onerror = (event) => {
            this.lastError = event.error;
            console.error("VOICE_ERROR:", event.error);
            this.isListening = false;

            if (event.error === 'not-allowed') {
                this.permissionStatus = 'denied';
            }

            this.onErrorCallback(event.error);
            this.onStateChangeCallback('error');
        };

        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join('');

            if (event.results[0].isFinal) {
                console.log("VOICE_RESULT_FINAL:", transcript);
                this.onResultCallback(transcript);
                this.onStateChangeCallback('transcribing');
            } else {
                // Real-time feedback for the UI
                this.onStateChangeCallback('listening', transcript);
            }
        };
    }

    async requestPermission() {
        try {
            console.log("VOICE: Requesting mic permission via getUserMedia...");
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            // Stop the stream immediately, we just wanted the permission
            stream.getTracks().forEach(track => track.stop());
            this.permissionStatus = 'granted';
            return true;
        } catch (err) {
            console.error("VOICE: Permission denied or hardware error:", err);
            this.permissionStatus = 'denied';
            return false;
        }
    }

    async toggle() {
        if (!this.recognition) {
            this.onErrorCallback('browser-unsupported');
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            // Priority: Check if we have permission first
            if (this.permissionStatus !== 'granted') {
                const ok = await this.requestPermission();
                if (!ok) {
                    this.onErrorCallback('mic-unavailable');
                    return;
                }
            }

            try {
                this.recognition.start();
            } catch (err) {
                console.error("VOICE: Failed to start recognition:", err);
                // Handle cases where it might already be started (listener conflict)
                if (err.name === 'InvalidStateError') {
                    this.recognition.stop();
                    setTimeout(() => this.recognition.start(), 100);
                }
            }
        }
    }

    speak(text) {
        if (!this.synth) return;

        this.synth.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = document.documentElement.lang || navigator.language || 'en-US';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        const voices = this.synth.getVoices();
        const preferredVoice = voices.find(v => v.lang.startsWith(utterance.lang) && (v.name.includes('Google') || v.name.includes('Natural')))
            || voices.find(v => v.lang.startsWith(utterance.lang))
            || voices[0];

        if (preferredVoice) utterance.voice = preferredVoice;

        utterance.onstart = () => this.onSpeechStartCallback();
        utterance.onend = () => this.onSpeechEndCallback();
        utterance.onerror = () => this.onSpeechEndCallback();

        this.synth.speak(utterance);
    }

    getSimpleStatus() {
        return {
            permission: this.permissionStatus,
            isListening: this.isListening,
            lastError: this.lastError,
            isSecure: window.isSecureContext
        };
    }
}

window.VoiceInterface = VoiceInterface;
