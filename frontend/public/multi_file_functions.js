// Multi-file Selection and Processing Functions

// Global variables for multi-file support
let selectedRecordings = new Map(); // filename -> {name, size_mb}

function toggleRecordingSelection(filename, sizeMB) {
    const selectBtn = document.getElementById(`select-${filename}`);
    
    if (selectedRecordings.has(filename)) {
        // Deselect
        selectedRecordings.delete(filename);
        selectBtn.innerHTML = '<i data-lucide="plus" style="width: 16px; height: 16px;"></i>';
        selectBtn.classList.remove('selected');
    } else {
        // Select
        selectedRecordings.set(filename, {
            name: filename,
            size_mb: sizeMB
        });
        selectBtn.innerHTML = '<i data-lucide="check" style="width: 16px; height: 16px;"></i>';
        selectBtn.classList.add('selected');
    }
    
    updateSelectedFilesDisplay();
    lucide.createIcons(); // Refresh icons
}

function updateSelectedFilesDisplay() {
    const selectedDisplay = document.getElementById('selected-files-display');
    const selectedList = document.getElementById('selected-files-list');
    const selectedSummary = document.getElementById('selected-files-summary');
    const transcribeBtn = document.getElementById('transcribe-btn');
    
    if (selectedRecordings.size === 0) {
        selectedDisplay.style.display = 'none';
        transcribeBtn.disabled = true;
        transcribeBtn.textContent = 'Select recordings to transcribe';
        return;
    }
    
    selectedDisplay.style.display = 'block';
    
    // Update file list
    let listHtml = '';
    let totalSize = 0;
    selectedRecordings.forEach((recording, filename) => {
        totalSize += recording.size_mb;
        listHtml += `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #eee;">
                <span style="font-size: 14px; color: #333;">${filename}</span>
                <span style="font-size: 12px; color: #666;">${recording.size_mb} MB</span>
            </div>
        `;
    });
    selectedList.innerHTML = listHtml;
    
    // Update summary
    selectedSummary.textContent = `${selectedRecordings.size} file(s) selected • ${totalSize.toFixed(2)} MB total`;
    
    // Update button
    transcribeBtn.disabled = false;
    transcribeBtn.textContent = `Transcribe ${selectedRecordings.size} file(s)`;
}

function clearSelectedFiles() {
    // Reset all selection buttons
    selectedRecordings.forEach((recording, filename) => {
        const selectBtn = document.getElementById(`select-${filename}`);
        if (selectBtn) {
            selectBtn.innerHTML = '<i data-lucide="plus" style="width: 16px; height: 16px;"></i>';
            selectBtn.classList.remove('selected');
        }
    });
    
    selectedRecordings.clear();
    updateSelectedFilesDisplay();
    lucide.createIcons(); // Refresh icons
}

function clearTranscriptionResults() {
    const resultsDiv = document.getElementById('transcription-results');
    const clearBtn = document.getElementById('clear-results-btn');
    
    if (resultsDiv) {
        resultsDiv.style.display = 'none';
        resultsDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #333;">Transcription Results</h3>
                <button onclick="toggleProcessLogs()" style="background: none; border: none; cursor: pointer; color: #666; margin-left: 8px; padding: 0;" title="Show processing logs">
                    <i data-lucide="info" style="width: 16px; height: 16px;"></i>
                </button>
            </div>
            
            <!-- Results will be populated here -->
            <div id="results-content"></div>
            
            <!-- Expandable Logs Section for Results -->
            <div id="results-process-logs" style="display: none; margin-bottom: 15px; text-align: left; background: #f8f9fa; padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 14px; border: 1px solid #ddd;">
                <div style="text-align: center; margin-bottom: 10px; font-weight: bold; color: #333;">Processing Logs</div>
                <div id="results-log-content" style="color: #555; line-height: 1.4;"></div>
            </div>
        `;
    }
    
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
    
    // Clear process logs
    clearProcessLogs();
}

async function transcribeSelectedFiles() {
    if (selectedRecordings.size === 0) {
        alert('Please select at least one recording first');
        return;
    }
    
    // Clear previous results
    clearTranscriptionResults();
    
    const filenames = Array.from(selectedRecordings.keys());
    
    try {
        console.log(`Starting transcription of ${filenames.length} files...`);
        
        // Show loading state
        const loadingDiv = document.getElementById('transcription-loading');
        const resultsDiv = document.getElementById('transcription-results');
        
        loadingDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        
        // Initialize logs
        clearProcessLogs();
        addProcessLog(`<i data-lucide="files" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Processing ${filenames.length} file(s)`);
        addProcessLog(`<i data-lucide="mic" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Initializing Whisper AI...`);
        
        let allResults = [];
        
        // Process each file
        for (let i = 0; i < filenames.length; i++) {
            const filename = filenames[i];
            const fileInfo = selectedRecordings.get(filename);
            
            addProcessLog(`<i data-lucide="play" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Processing ${i + 1}/${filenames.length}: ${filename}`);
            addProcessLog(`<i data-lucide="file" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>File size: ${fileInfo.size_mb} MB`);
            
            // Call the transcription API endpoint
            const response = await fetch('/api/ai/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: filename,
                    mode: 'llama'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                result.filename = filename; // Add filename to result
                allResults.push(result);
                
                addProcessLog(`<i data-lucide="check" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Completed ${filename}`);
            } else {
                const errorText = await response.text();
                console.error(`Transcription failed for ${filename}:`, errorText);
                addProcessLog(`<i data-lucide="x" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Failed ${filename}: ${errorText}`);
                
                // Add error result
                allResults.push({
                    filename: filename,
                    success: false,
                    error: errorText
                });
            }
        }
        
        // Display all results
        addProcessLog(`<i data-lucide="check-circle" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>All files processed`);
        displayMultipleTranscriptionResults(allResults);
        
    } catch (error) {
        console.error('Transcription error:', error);
        addProcessLog(`<i data-lucide="x" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Error: ${error.message}`);
        alert('Transcription failed. Check the logs for details.');
    } finally {
        // Hide loading state
        document.getElementById('transcription-loading').style.display = 'none';
        lucide.createIcons(); // Refresh icons
    }
}

function displayMultipleTranscriptionResults(results) {
    const resultsDiv = document.getElementById('transcription-results');
    const resultsContent = document.getElementById('results-content');
    const clearBtn = document.getElementById('clear-results-btn');
    
    if (!resultsDiv || !resultsContent) return;
    
    let contentHtml = '';
    
    results.forEach((result, index) => {
        if (result.success === false) {
            // Error result
            contentHtml += `
                <div style="background: #fee; border: 1px solid #fcc; padding: 12px; border-radius: 6px; margin-bottom: 15px; font-size: 14px;">
                    <div style="font-weight: 500; color: #c53030; margin-bottom: 8px;">
                        <i data-lucide="x-circle" style="width: 16px; height: 16px; display: inline-block; margin-right: 6px;"></i>
                        ${result.filename} - Processing Failed
                    </div>
                    <div style="color: #666;">Error: ${result.error}</div>
                </div>
            `;
        } else {
            // Success result
            contentHtml += `
                <div style="background: #f8f9fa; border: 1px solid #e9ecef; padding: 12px; border-radius: 6px; margin-bottom: 15px; font-size: 14px;">
                    <div style="font-weight: 500; color: #333; margin-bottom: 8px; display: flex; align-items: center;">
                        <i data-lucide="file-audio" style="width: 16px; height: 16px; display: inline-block; margin-right: 6px;"></i>
                        ${result.filename}
                        ${result.detected_language ? `<span style="margin-left: 8px; font-size: 12px; background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 4px;">${result.detected_language}</span>` : ''}
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                        <strong style="color: #333;">Transcript:</strong>
                        <div style="color: #333; margin-top: 4px;">
                            ${result.transcription || 'No transcription available'}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                        <strong style="color: #333;">Sentiment:</strong>
                        <span style="color: #555; margin-left: 8px;">
                            ${result.sentiment || 'neutral'}
                        </span>
                    </div>
                    
                    <div>
                        <strong style="color: #333;">Brutal Honest Reply:</strong>
                        <div style="color: #555; margin-top: 4px; line-height: 1.4;">
                            ${result.brutal_honesty || 'Analysis not available'}
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    resultsContent.innerHTML = contentHtml;
    resultsDiv.style.display = 'block';
    clearBtn.style.display = 'inline-flex';
    
    lucide.createIcons(); // Refresh icons
}

// Make functions globally available
window.toggleRecordingSelection = toggleRecordingSelection;
window.clearSelectedFiles = clearSelectedFiles;
window.clearTranscriptionResults = clearTranscriptionResults;
window.transcribeSelectedFiles = transcribeSelectedFiles;
