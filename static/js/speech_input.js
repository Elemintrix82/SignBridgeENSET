/**
 * SignBridge — SpeechInput
 * Web Speech API (reconnaissance vocale navigateur)
 */
class SpeechInput {
  constructor(targetInputId, onUpdateCallback) {
    this.targetInput  = document.getElementById(targetInputId);
    this.onUpdate     = onUpdateCallback || (() => {});
    this.recognition  = null;
    this.isListening  = false;
    this._interim     = '';

    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.warn('Web Speech API non supportée dans ce navigateur');
      return;
    }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SR();
    this.recognition.lang            = 'fr-FR';
    this.recognition.continuous      = true;
    this.recognition.interimResults  = true;
    this.recognition.maxAlternatives = 1;

    this.recognition.onresult = (event) => {
      let final   = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript + ' ';
        } else {
          interim += transcript;
        }
      }

      if (final && this.targetInput) {
        this.targetInput.value += final;
        this.onUpdate();
      }
      this._interim = interim;
    };

    this.recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        window.toast?.error('Microphone non autorisé — vérifiez les permissions');
      } else if (event.error !== 'no-speech') {
        console.warn('Speech error:', event.error);
      }
      this.isListening = false;
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        // Restart if still supposed to be listening
        try { this.recognition.start(); } catch (e) {}
      }
    };
  }

  start() {
    if (!this.recognition) {
      window.toast?.error('Reconnaissance vocale non disponible dans ce navigateur');
      return false;
    }
    try {
      this.recognition.start();
      this.isListening = true;
      return true;
    } catch (e) {
      console.error('Speech start error:', e);
      return false;
    }
  }

  stop() {
    if (!this.recognition) return;
    this.isListening = false;
    try {
      this.recognition.stop();
    } catch (e) {}
  }

  toggle() {
    if (this.isListening) {
      this.stop(); return false;
    } else {
      return this.start();
    }
  }

  static isSupported() {
    return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
  }
}
