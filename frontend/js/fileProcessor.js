class FileProcessor {
    static supportedFormats = ['.csv', '.txt', '.json'];
    static maxFileSize = 50 * 1024 * 1024; // 50MB

    static validateFile(file) {
        const errors = [];

        // Check file type
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.supportedFormats.includes(fileExtension)) {
            errors.push(`Formato no soportado: ${fileExtension}. Use: ${this.supportedFormats.join(', ')}`);
        }

        // Check file size
        if (file.size > this.maxFileSize) {
            errors.push(`Archivo demasiado grande: ${this.formatFileSize(file.size)}. Máximo: ${this.formatFileSize(this.maxFileSize)}`);
        }

        // Check if file is empty
        if (file.size === 0) {
            errors.push('El archivo está vacío');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    static async parseFile(file) {
        const validation = this.validateFile(file);
        if (!validation.isValid) {
            throw new Error(validation.errors.join(', '));
        }

        try {
            const content = await this.readFileContent(file);
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

            switch (fileExtension) {
                case '.csv':
                    return this.parseCSV(content);
                case '.txt':
                    return this.parseTXT(content);
                case '.json':
                    return this.parseJSON(content);
                default:
                    throw new Error(`Parser no implementado para: ${fileExtension}`);
            }
        } catch (error) {
            window.APP_LOGGER.error('Error parsing file:', error);
            throw new Error(`Error procesando archivo: ${error.message}`);
        }
    }

    static readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = () => reject(new Error('Error leyendo el archivo'));
            reader.readAsText(file);
        });
    }

    static parseCSV(content) {
        try {
            const lines = content.split('\n').filter(line => line.trim() !== '');
            const data = {
                ppm: [],
                intensity: []
            };

            lines.forEach((line, index) => {
                // Skip header lines that don't start with numbers
                if (index === 0 && !this.isNumericLine(line)) {
                    return;
                }

                const values = line.split(',').map(val => val.trim());
                if (values.length >= 2) {
                    const ppm = parseFloat(values[0]);
                    const intensity = parseFloat(values[1]);

                    if (!isNaN(ppm) && !isNaN(intensity)) {
                        data.ppm.push(ppm);
                        data.intensity.push(intensity);
                    }
                }
            });

            if (data.ppm.length === 0) {
                throw new Error('No se encontraron datos válidos en el archivo CSV');
            }

            window.APP_LOGGER.debug(`Parsed CSV: ${data.ppm.length} data points`);
            return data;

        } catch (error) {
            throw new Error(`Error parsing CSV: ${error.message}`);
        }
    }

    static parseTXT(content) {
        try {
            const lines = content.split('\n').filter(line => line.trim() !== '');
            const data = {
                ppm: [],
                intensity: []
            };

            // Try different delimiters
            const delimiters = ['\t', ' ', ',', ';'];
            let delimiter = null;

            // Detect delimiter from first data line
            for (const delim of delimiters) {
                const firstLine = lines.find(line => this.isNumericLine(line));
                if (firstLine && firstLine.split(delim).length >= 2) {
                    delimiter = delim;
                    break;
                }
            }

            if (!delimiter) {
                throw new Error('No se pudo detectar el delimitador del archivo');
            }

            lines.forEach((line, index) => {
                // Skip header lines
                if (index === 0 && !this.isNumericLine(line)) {
                    return;
                }

                const values = line.split(delimiter).map(val => val.trim()).filter(val => val !== '');
                if (values.length >= 2) {
                    const ppm = parseFloat(values[0]);
                    const intensity = parseFloat(values[1]);

                    if (!isNaN(ppm) && !isNaN(intensity)) {
                        data.ppm.push(ppm);
                        data.intensity.push(intensity);
                    }
                }
            });

            if (data.ppm.length === 0) {
                throw new Error('No se encontraron datos válidos en el archivo TXT');
            }

            window.APP_LOGGER.debug(`Parsed TXT with delimiter "${delimiter}": ${data.ppm.length} data points`);
            return data;

        } catch (error) {
            throw new Error(`Error parsing TXT: ${error.message}`);
        }
    }

    static parseJSON(content) {
        try {
            const data = JSON.parse(content);
            
            // Support different JSON structures
            if (data.spectrum && data.spectrum.ppm && data.spectrum.intensity) {
                // Craft/Mnova format
                return {
                    ppm: data.spectrum.ppm,
                    intensity: data.spectrum.intensity
                };
            } else if (data.ppm && data.intensity) {
                // Direct format
                return data;
            } else if (Array.isArray(data) && data.length > 0 && data[0].x !== undefined && data[0].y !== undefined) {
                // Array of points format
                return {
                    ppm: data.map(point => point.x),
                    intensity: data.map(point => point.y)
                };
            } else {
                throw new Error('Formato JSON no reconocido');
            }

        } catch (error) {
            throw new Error(`Error parsing JSON: ${error.message}`);
        }
    }

    static isNumericLine(line) {
        const firstValue = line.split(/[\t, ;]/)[0];
        return !isNaN(parseFloat(firstValue)) && isFinite(firstValue);
    }

    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    static async createFilePreview(file, maxPoints = 1000) {
        try {
            const data = await this.parseFile(file);
            
            // Downsample for preview if too many points
            if (data.ppm.length > maxPoints) {
                const step = Math.ceil(data.ppm.length / maxPoints);
                data.ppm = data.ppm.filter((_, index) => index % step === 0);
                data.intensity = data.intensity.filter((_, index) => index % step === 0);
            }

            return data;

        } catch (error) {
            window.APP_LOGGER.error('Error creating file preview:', error);
            throw error;
        }
    }

    static getFileInfo(file) {
        return {
            name: file.name,
            size: this.formatFileSize(file.size),
            type: file.type || 'Unknown',
            lastModified: new Date(file.lastModified).toLocaleString(),
            extension: '.' + file.name.split('.').pop().toLowerCase()
        };
    }

    static async validateSpectrumData(data) {
        const warnings = [];

        if (!data.ppm || !data.intensity) {
            throw new Error('Datos de espectro incompletos');
        }

        if (data.ppm.length !== data.intensity.length) {
            throw new Error('Los arrays ppm e intensidad tienen longitudes diferentes');
        }

        if (data.ppm.length < 10) {
            warnings.push('El espectro tiene muy pocos puntos de datos');
        }

        // Check if ppm is in reasonable range for NMR
        const minPPM = Math.min(...data.ppm);
        const maxPPM = Math.max(...data.ppm);
        
        if (minPPM < -200 || maxPPM > 200) {
            warnings.push('El rango de ppm parece fuera de lo común para RMN');
        }

        // Check for constant values (potential issues)
        const uniqueIntensities = new Set(data.intensity.map(v => v.toFixed(2)));
        if (uniqueIntensities.size < 10) {
            warnings.push('Los datos de intensidad muestran poca variación');
        }

        return {
            isValid: true,
            warnings: warnings,
            stats: {
                dataPoints: data.ppm.length,
                ppmRange: { min: minPPM, max: maxPPM },
                intensityRange: { 
                    min: Math.min(...data.intensity), 
                    max: Math.max(...data.intensity) 
                }
            }
        };
    }
}