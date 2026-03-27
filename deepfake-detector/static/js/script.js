/* ========================================
   DEEPFAKE DETECTOR - MODERN INTERACTIONS
   ======================================== */

// State Management
const state = {
    files: [],
    currentResults: [],
    isAnalyzing: false,
    modelsReady: false,
    notifications: [],
    darkMode: true
};

// DOM Elements
const elements = {
    fileInput: document.getElementById('fileInput'),
    uploadArea: document.getElementById('uploadArea'),
    fileList: document.getElementById('fileList'),
    filesGrid: document.getElementById('filesGrid'),
    fileCount: document.getElementById('fileCount'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    batchBtn: document.getElementById('batchBtn'),
    resetBtn: document.getElementById('resetBtn'),
    resultsSection: document.getElementById('resultsSection'),
    resultsContainer: document.getElementById('resultsContainer'),
    recentGrid: document.getElementById('recentGrid'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),
    modelStatus: document.getElementById('modelStatus')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadRecentResults();
    checkSystemStatus();
    initDragAndDrop();
    initTooltips();
});

function initEventListeners() {
    // File input
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Buttons
    elements.analyzeBtn.addEventListener('click', () => handleAnalyze());
    elements.batchBtn.addEventListener('click', () => handleBatchAnalyze());
    elements.resetBtn.addEventListener('click', handleReset);
    
    // Export buttons
    const pdfBtn = document.getElementById('downloadPDF');
    if (pdfBtn) {
        pdfBtn.addEventListener('click', handlePDFDownload);
    }
}

function initDragAndDrop() {
    const uploadArea = elements.uploadArea;
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        addFiles(files);
    });
}

function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
        el.addEventListener('mouseenter', showTooltip);
        el.addEventListener('mouseleave', hideTooltip);
    });
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function addFiles(files) {
    const validFiles = files.filter(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        const validExts = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'mp4', 'avi', 'mov', 'mkv'];
        return validExts.includes(ext);
    });
    
    if (validFiles.length === 0) {
        showNotification('Please upload valid image or video files', 'error');
        return;
    }
    
    state.files.push(...validFiles);
    updateFileList();
    updateButtons();
    
    showNotification(`${validFiles.length} file(s) added`, 'success');
}

function updateFileList() {
    if (state.files.length === 0) {
        elements.fileList.style.display = 'none';
        return;
    }
    
    elements.fileList.style.display = 'block';
    elements.fileCount.textContent = state.files.length;
    
    elements.filesGrid.innerHTML = state.files.map((file, index) => `
        <div class="file-item fade-in" data-index="${index}">
            <div class="file-icon">
                <i class="fas ${file.type.startsWith('image/') ? 'fa-image' : 'fa-video'}"></i>
            </div>
            <div class="file-info">
                <div class="file-name">${truncateText(file.name, 40)}</div>
                <div class="file-meta">
                    <span><i class="fas fa-database"></i> ${formatFileSize(file.size)}</span>
                    <span><i class="fas ${file.type.startsWith('image/') ? 'fa-camera' : 'fa-play'}"></i> ${file.type.startsWith('image/') ? 'Image' : 'Video'}</span>
                </div>
            </div>
            <div class="file-actions">
                <button onclick="previewFile(${index})" title="Preview">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="removeFile(${index})" title="Remove">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function updateButtons() {
    elements.analyzeBtn.disabled = state.files.length === 0 || state.isAnalyzing;
    elements.batchBtn.disabled = state.files.length < 2 || state.isAnalyzing;
}

async function handleAnalyze() {
    if (state.files.length === 0 || state.isAnalyzing) return;
    await analyzeFiles([state.files[0]]);
}

async function handleBatchAnalyze() {
    if (state.files.length < 2 || state.isAnalyzing) return;
    await analyzeFiles(state.files);
}

async function analyzeFiles(files) {
    state.isAnalyzing = true;
    updateButtons();
    showLoading(true);
    
    const results = [];
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const progress = ((i + 1) / files.length) * 100;
        
        updateLoadingProgress(progress, `Analyzing ${truncateText(file.name, 30)} (${i+1}/${files.length})`);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/analyze', { method: 'POST', body: formData });
            const result = await response.json();
            
            if (response.ok) {
                results.push(result);
                showNotification(`${file.name}: ${result.is_fake ? 'FAKE' : 'REAL'} (${(result.confidence * 100).toFixed(1)}%)`, 
                    result.is_fake ? 'warning' : 'success');
            } else {
                results.push({ error: result.error, filename: file.name });
                showNotification(`Failed: ${file.name}`, 'error');
            }
        } catch (error) {
            results.push({ error: error.message, filename: file.name });
            showNotification(`Error: ${file.name}`, 'error');
        }
    }
    
    state.currentResults = results;
    
    if (results.length === 1) {
        displaySingleResult(results[0]);
    } else {
        displayBatchResults(results);
    }
    
    showLoading(false);
    state.isAnalyzing = false;
    updateButtons();
    loadRecentResults();
}

function displaySingleResult(result) {
    if (result.error) {
        elements.resultsContainer.innerHTML = `<div class="error">Error: ${result.error}</div>`;
        return;
    }
    
    const isFake = result.is_fake;
    const confidence = (result.confidence * 100).toFixed(1);
    const probability = (result.probability * 100).toFixed(1);
    const time = new Date(result.analysis_time).toLocaleString();
    
    elements.resultsSection.style.display = 'block';
    elements.resultsContainer.innerHTML = `
        <div class="result-card fade-in">
            <div class="result-header">
                <div class="result-status">
                    <div class="status-icon ${isFake ? 'fake' : 'real'}">
                        <i class="fas ${isFake ? 'fa-exclamation-triangle' : 'fa-check-circle'}"></i>
                    </div>
                    <div class="status-text ${isFake ? 'fake' : 'real'}">
                        ${isFake ? '⚠️ DEEPFAKE DETECTED' : '✅ AUTHENTIC MEDIA'}
                    </div>
                </div>
                <div class="confidence-badge">
                    <i class="fas fa-chart-line"></i> ${confidence}% Confidence
                </div>
            </div>
            
            <div class="probability-meter">
                <div class="meter-label">
                    <span>Fake Probability</span>
                    <span>${probability}%</span>
                </div>
                <div class="meter-bar">
                    <div class="meter-fill ${isFake ? 'fake' : 'real'}" style="width: ${probability}%"></div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <i class="fas fa-microchip"></i>
                    <div class="stat-label">Model Used</div>
                    <div class="stat-value">${result.model_used || 'Ensemble'}</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-database"></i>
                    <div class="stat-label">File Size</div>
                    <div class="stat-value">${result.file_info?.size_mb || 'N/A'} MB</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-clock"></i>
                    <div class="stat-label">Analysis Time</div>
                    <div class="stat-value">${time}</div>
                </div>
            </div>
            
            ${result.scores ? `
                <div class="model-scores">
                    <h4><i class="fas fa-chart-simple"></i> Model Breakdown</h4>
                    ${Object.entries(result.scores).map(([model, score]) => `
                        <div class="score-item">
                            <div class="score-name">${getModelName(model)}</div>
                            <div class="score-bar-container">
                                <div class="score-bar" style="width: ${score * 100}%"></div>
                            </div>
                            <div class="score-value">${(score * 100).toFixed(1)}%</div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${result.frames_analyzed ? `
                <div class="model-scores">
                    <h4><i class="fas fa-video"></i> Video Analysis</h4>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Frames Analyzed</div>
                            <div class="stat-value">${result.frames_analyzed}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Consistency</div>
                            <div class="stat-value">${(result.consistency * 100).toFixed(1)}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Std Deviation</div>
                            <div class="stat-value">${(result.std_deviation * 100).toFixed(1)}%</div>
                        </div>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function displayBatchResults(results) {
    const validResults = results.filter(r => !r.error);
    const fakeCount = validResults.filter(r => r.is_fake).length;
    const realCount = validResults.length - fakeCount;
    const avgConfidence = validResults.reduce((sum, r) => sum + r.confidence, 0) / validResults.length;
    
    elements.resultsSection.style.display = 'block';
    elements.resultsContainer.innerHTML = `
        <div class="section-header">
            <h2><i class="fas fa-chart-bar"></i> Batch Results</h2>
            <div class="stats-badges">
                <div class="stat-badge">
                    <i class="fas fa-chart-line"></i>
                    <span>${validResults.length} Analyzed</span>
                </div>
                <div class="stat-badge" style="border-left-color: var(--danger)">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${fakeCount} DeepFakes</span>
                </div>
                <div class="stat-badge" style="border-left-color: var(--success)">
                    <i class="fas fa-check-circle"></i>
                    <span>${realCount} Authentic</span>
                </div>
                <div class="stat-badge">
                    <i class="fas fa-percentage"></i>
                    <span>${(avgConfidence * 100).toFixed(1)}% Avg Conf</span>
                </div>
            </div>
        </div>
        
        <div class="batch-results">
            ${validResults.map(result => `
                <div class="recent-item" onclick="viewResult('${result.result_id}')">
                    <div class="recent-icon ${result.is_fake ? 'fake' : 'real'}">
                        <i class="fas ${result.is_fake ? 'fa-exclamation-triangle' : 'fa-check-circle'}"></i>
                    </div>
                    <div class="recent-info">
                        <div class="recent-filename">${truncateText(result.filename, 40)}</div>
                        <div class="recent-meta">
                            <span>${result.is_fake ? 'DeepFake' : 'Authentic'}</span>
                            <span>${(result.confidence * 100).toFixed(1)}% confidence</span>
                        </div>
                    </div>
                    <div class="recent-confidence">${(result.probability * 100).toFixed(1)}%</div>
                </div>
            `).join('')}
        </div>
    `;
}

async function loadRecentResults() {
    try {
        const response = await fetch('/api/results?limit=5');
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            elements.recentGrid.innerHTML = data.results.map(result => `
                <div class="recent-item fade-in" onclick="viewResult('${result.result_id}')">
                    <div class="recent-icon ${result.is_fake ? 'fake' : 'real'}">
                        <i class="fas ${result.is_fake ? 'fa-exclamation-triangle' : 'fa-check-circle'}"></i>
                    </div>
                    <div class="recent-info">
                        <div class="recent-filename">${truncateText(result.filename, 40)}</div>
                        <div class="recent-meta">
                            <span>${new Date(result.analysis_time).toLocaleDateString()}</span>
                            <span>${(result.confidence * 100).toFixed(1)}% confidence</span>
                        </div>
                    </div>
                    <div class="recent-confidence">${result.is_fake ? 'FAKE' : 'REAL'}</div>
                </div>
            `).join('');
        } else {
            elements.recentGrid.innerHTML = '<div class="loading-placeholder">No recent analyses. Upload a file to get started!</div>';
        }
    } catch (error) {
        console.error('Error loading recent results:', error);
        elements.recentGrid.innerHTML = '<div class="loading-placeholder">Failed to load recent results</div>';
    }
}

async function checkSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.models_loaded > 0) {
            elements.modelStatus.innerHTML = `
                <span class="status-dot"></span>
                <span>${data.models_loaded} Models Ready</span>
            `;
            state.modelsReady = true;
        } else {
            elements.modelStatus.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading Models...</span>
            `;
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

async function exportResults(format) {
    if (state.currentResults.length === 0) {
        showNotification('No results to export', 'error');
        return;
    }
    
    let data, filename, mimeType;
    
    if (format === 'json') {
        data = JSON.stringify(state.currentResults, null, 2);
        filename = `deepfake_results_${Date.now()}.json`;
        mimeType = 'application/json';
    } else {
        const headers = ['Filename', 'Is Fake', 'Probability', 'Confidence', 'Media Type', 'Analysis Time'];
        const rows = state.currentResults.map(r => [
            r.filename,
            r.is_fake ? 'FAKE' : 'REAL',
            (r.probability * 100).toFixed(2) + '%',
            (r.confidence * 100).toFixed(2) + '%',
            r.media_type,
            new Date(r.analysis_time).toLocaleString()
        ]);
        
        const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
        data = csvContent;
        filename = `deepfake_results_${Date.now()}.csv`;
        mimeType = 'text/csv';
    }
    
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification(`Exported ${state.currentResults.length} results to ${format.toUpperCase()}`, 'success');
}

function handleReset() {
    state.files = [];
    state.currentResults = [];
    elements.fileInput.value = '';
    updateFileList();
    updateButtons();
    elements.resultsSection.style.display = 'none';
    showNotification('Reset complete', 'info');
}

function previewFile(index) {
    const file = state.files[index];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Preview: ${truncateText(file.name, 40)}</h3>
                    <button class="notification-close" onclick="this.closest('.modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${file.type.startsWith('image/') ? 
                        `<img src="${e.target.result}" alt="Preview">` : 
                        `<video controls autoplay src="${e.target.result}"></video>`
                    }
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    };
    reader.readAsDataURL(file);
}

function removeFile(index) {
    state.files.splice(index, 1);
    updateFileList();
    updateButtons();
    
    if (state.files.length === 0) {
        elements.fileList.style.display = 'none';
    }
}

function viewResult(resultId) {
    window.location.href = `/result/${resultId}`;
}

function showLoading(show, text = 'Analyzing media...') {
    if (show) {
        elements.loadingOverlay.classList.add('active');
        elements.loadingText.textContent = text;
    } else {
        elements.loadingOverlay.classList.remove('active');
    }
}

function updateLoadingProgress(percent, text) {
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) progressFill.style.width = `${percent}%`;
    if (text) elements.loadingText.textContent = text;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
        </div>
        <div class="notification-message">${message}</div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

function getModelName(modelKey) {
    const names = {
        'swinv2': 'SwinV2',
        'efficientnet': 'EfficientNet',
        'xception': 'XceptionNet',
        'vit': 'Vision Transformer'
    };
    return names[modelKey] || modelKey;
}

// Add this function to your script.js (replace the existing one)

function handlePDFDownload() {
    // Check if there are any results
    if (!state.currentResults || state.currentResults.length === 0) {
        showNotification("No results to download. Please analyze an image first.", "error");
        return;
    }
    
    // Get the most recent result
    const result = state.currentResults[0];
    
    // Check if result has the required data
    if (!result || !result.filename) {
        showNotification("Invalid result data. Please analyze again.", "error");
        return;
    }
    
    // Show loading state on button
    const pdfBtn = document.getElementById('downloadPDF');
    if (!pdfBtn) {
        console.error("PDF button not found");
        return;
    }
    
    const originalText = pdfBtn.innerHTML;
    pdfBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
    pdfBtn.disabled = true;
    
    // Prepare data for PDF with thumbnail info
    const pdfData = {
        filename: result.filename || 'analysis_result',
        label: result.is_fake ? 'FAKE' : 'REAL',
        probability: result.probability || 0,
        confidence: result.confidence || 0,
        media_type: result.media_type || 'image',
        model_used: result.model_used || 'Ensemble Model',
        analysis_time: result.analysis_time || new Date().toISOString(),
        scores: result.scores || {},
        reasoning: result.reasoning || 'Analysis completed successfully',
        file_info: result.file_info || {},
        thumbnail_path: result.thumbnail_path || null,  // Add thumbnail path
        frames_analyzed: result.frames_analyzed,
        consistency: result.consistency
    };
    
    // Send request to generate PDF
    fetch('/download_pdf', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(pdfData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'PDF generation failed');
            });
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${result.filename.replace(/\.[^/.]+$/, '')}_report.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification("PDF report downloaded successfully!", "success");
    })
    .catch(error => {
        console.error("PDF error:", error);
        showNotification(`PDF download failed: ${error.message}`, "error");
    })
    .finally(() => {
        pdfBtn.innerHTML = originalText;
        pdfBtn.disabled = false;
    });
}

// IMPORTANT: make it global
window.downloadPDF = downloadPDF;
// Make functions globally accessible
window.previewFile = previewFile;
window.removeFile = removeFile;
window.viewResult = viewResult;
window.exportResults = exportResults;