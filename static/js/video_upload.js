/**
 * SignBridge — VideoUpload
 * Gestion de l'import vidéo ASL → traduction texte via API
 */
class VideoUpload {
  constructor(options = {}) {
    this.apiUrl       = options.apiUrl || '/api/translate/video-to-text/';
    this.onProgress   = options.onProgress   || (() => {});
    this.onComplete   = options.onComplete   || (() => {});
    this.onError      = options.onError      || (() => {});
    this.maxSizeMB    = options.maxSizeMB    || 100;
    this.allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/webm', 'video/x-msvideo'];
  }

  openFilePicker() {
    const input = document.createElement('input');
    input.type   = 'file';
    input.accept = 'video/mp4,video/avi,video/quicktime,video/webm,.mp4,.avi,.mov,.webm';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) this.upload(file);
    };
    input.click();
  }

  validate(file) {
    if (!file) return { ok: false, error: 'Aucun fichier sélectionné' };

    const maxBytes = this.maxSizeMB * 1024 * 1024;
    if (file.size > maxBytes) {
      return { ok: false, error: `Fichier trop volumineux (max ${this.maxSizeMB} Mo)` };
    }

    if (!this.allowedTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|webm)$/i)) {
      return { ok: false, error: 'Format non supporté. Utilisez MP4, AVI, MOV ou WebM.' };
    }

    return { ok: true };
  }

  async upload(file) {
    const validation = this.validate(file);
    if (!validation.ok) {
      this.onError(validation.error);
      window.toast?.error(validation.error);
      return;
    }

    this.onProgress(5, 'Envoi de la vidéo...');

    const formData = new FormData();
    formData.append('video', file);

    const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

    try {
      this.onProgress(15, 'Traitement en cours...');

      const xhr = new XMLHttpRequest();
      xhr.open('POST', this.apiUrl);
      xhr.setRequestHeader('X-CSRFToken', csrfToken);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 40);
          this.onProgress(10 + pct, 'Envoi ' + (10 + pct) + '%...');
        }
      };

      xhr.onload = () => {
        if (xhr.status === 200) {
          try {
            const data = JSON.parse(xhr.responseText);
            this.onProgress(100, 'Terminé');
            this.onComplete(data);
            window.toast?.success('Vidéo analysée — ' + (data.nb_words || 0) + ' signe(s) reconnu(s)');
          } catch (e) {
            this.onError('Réponse serveur invalide');
            window.toast?.error('Erreur de traitement');
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            this.onError(err.error || 'Erreur serveur');
            window.toast?.error(err.error || 'Erreur lors du traitement de la vidéo');
          } catch {
            this.onError('Erreur serveur ' + xhr.status);
            window.toast?.error('Erreur serveur');
          }
        }
      };

      xhr.onerror = () => {
        this.onError('Erreur réseau');
        window.toast?.error('Erreur de connexion');
      };

      // Simulate processing progress
      this.onProgress(50, 'Extraction des landmarks...');
      setTimeout(() => this.onProgress(70, 'Classification des signes...'), 1000);
      setTimeout(() => this.onProgress(85, 'Post-traitement...'), 2000);

      xhr.send(formData);

    } catch (err) {
      this.onError(err.message || 'Erreur inattendue');
      window.toast?.error('Erreur lors de l\'envoi');
    }
  }

  static formatFileSize(bytes) {
    if (bytes < 1024)       return bytes + ' o';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko';
    return (bytes / (1024 * 1024)).toFixed(1) + ' Mo';
  }
}
