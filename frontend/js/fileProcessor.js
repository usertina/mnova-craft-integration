// ============================================================================
// FILE PROCESSOR - Gestión de archivos
// ============================================================================

class FileProcessor {
    static currentFile = null;

    static handleFileSelect(files) {
        if (!files || files.length === 0) {
            window.APP_LOGGER.warn('[FileProcessor] No files selected');
            return;
        }

        const file = files[0];
        this.currentFile = file;

        window.APP_LOGGER.info(`[FileProcessor] Archivo seleccionado: ${file.name}`);
        
        // Actualizar UI
        const fileInfo = document.getElementById('fileInfo');
        if (fileInfo) {
            fileInfo.innerHTML = `
                <i class="fas fa-file-alt"></i>
                <span>${UIManager.escapeHtml(file.name)}</span>
                <span class="file-size">(${this.formatFileSize(file.size)})</span>
            `;
            fileInfo.style.display = 'flex';
        }

        // Habilitar botón de análisis
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
        }

        UIManager.showNotification(
            `Archivo cargado: ${file.name}`,
            'success'
        );
    }

    static getCurrentFile() {
        return this.currentFile;
    }

    static clearFiles() {
        this.currentFile = null;
        
        const fileInfo = document.getElementById('fileInfo');
        if (fileInfo) {
            fileInfo.style.display = 'none';
        }

        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.value = '';
        }

        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.disabled = true;
        }
    }

    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Hacer disponible globalmente
window.FileProcessor = FileProcessor;