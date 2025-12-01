// Home Page Functions - Brutally Honest AI
// Tab switching and recording history
// Notifications use design-system.css via notifications.js

// ============================================
// TAB SWITCHING
// ============================================

function switchTab(tabName) {
  console.log('Switching to tab:', tabName);
  
  // Update tab buttons
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.tab === tabName);
  });
  
  // Update tab content visibility
  document.querySelectorAll('[id^="tab-content-"]').forEach(content => {
    const isActive = content.id === `tab-content-${tabName}`;
    if (isActive) {
      // For record tab, use flex; for others, use block
      if (content.id === 'tab-content-record') {
        content.style.display = 'flex';
      } else {
        content.style.display = 'block';
      }
      content.classList.add('active');
    } else {
      content.style.display = 'none';
      content.classList.remove('active');
    }
  });
  
  // Update URL hash
  window.location.hash = tabName;
  
  // Load history if switching to history tab
  if (tabName === 'history') {
    loadTranscriptionHistory();
  }
  
  // Scan devices if switching to device tab
  if (tabName === 'device' && typeof scanForDevices === 'function') {
    scanForDevices();
  }
}

// ============================================
// RECORDING UI
// ============================================

function updateRecordingUI(recording) {
  const recordBtn = document.getElementById('record-btn');
  const recordText = document.getElementById('record-text');
  const recordIcon = recordBtn?.querySelector('.record-icon');
  const stopIcon = recordBtn?.querySelector('.stop-icon');
  const indicator = document.getElementById('recording-indicator');
  const hint = document.getElementById('record-hint');
  
  if (recordBtn) {
    if (recording) {
      recordBtn.classList.add('recording');
      if (recordText) recordText.textContent = 'Tap to Stop';
      if (recordIcon) recordIcon.style.display = 'none';
      if (stopIcon) stopIcon.style.display = 'inline-block';
      if (indicator) indicator.style.display = 'flex';
      if (hint) hint.textContent = 'Recording in progress... Tap again to stop.';
      if (window.showNotification) window.showNotification('info', 'Recording started');
    } else {
      recordBtn.classList.remove('recording');
      if (recordText) recordText.textContent = 'Tap to Record';
      if (recordIcon) recordIcon.style.display = 'inline-block';
      if (stopIcon) stopIcon.style.display = 'none';
      if (indicator) indicator.style.display = 'none';
      if (hint) hint.textContent = 'Press the button to start recording. Your recording will be automatically saved.';
    }
  }
}

// ============================================
// HISTORY FUNCTIONS
// ============================================

// Store full history data for filtering
let historyData = [];

async function loadTranscriptionHistory() {
  const historyList = document.getElementById('history-list');
  if (!historyList) return;
  
  historyList.innerHTML = '<div class="text-center text-muted p-4">Loading...</div>';
  
  try {
    const response = await fetch('/api/transcription-history');
    const data = await response.json();
    
    // Store data for filtering
    historyData = data.history || [];
    
    // Apply current filters and render
    filterHistory();
    
  } catch (error) {
    console.error('Error loading history:', error);
    historyList.innerHTML = '<div class="history-empty-state"><p>Failed to load history</p></div>';
    updateHistoryCount(0);
  }
}

function filterHistory() {
  const searchTerm = (document.getElementById('history-search')?.value || '').toLowerCase();
  const statusFilter = document.getElementById('history-status-filter')?.value || '';
  const sentimentFilter = document.getElementById('history-sentiment-filter')?.value || '';
  const sortOrder = document.getElementById('history-sort')?.value || 'newest';
  
  let filtered = [...historyData];
  
  // Search filter
  if (searchTerm) {
    filtered = filtered.filter(item => {
      const filename = (item.originalFilename || item.filename || item.savedFilename || '').toLowerCase();
      const transcription = (item.result?.transcription || '').toLowerCase();
      const keywords = (item.result?.keywords || []).join(' ').toLowerCase();
      return filename.includes(searchTerm) || transcription.includes(searchTerm) || keywords.includes(searchTerm);
    });
  }
  
  // Status filter
  if (statusFilter) {
    filtered = filtered.filter(item => {
      const hasResult = item.result && item.result.transcription;
      const status = hasResult ? 'completed' : (item.status || 'pending');
      return status === statusFilter;
    });
  }
  
  // Sentiment filter
  if (sentimentFilter) {
    filtered = filtered.filter(item => {
      const sentiment = item.result?.sentiment || '';
      return sentiment.toLowerCase() === sentimentFilter;
    });
  }
  
  // Sort
  filtered.sort((a, b) => {
    const dateA = new Date(a.timestamp);
    const dateB = new Date(b.timestamp);
    return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
  });
  
  // Render filtered results
  renderHistoryItems(filtered);
  updateHistoryCount(filtered.length);
}

function updateHistoryCount(count) {
  const countEl = document.getElementById('history-count');
  if (countEl) {
    countEl.textContent = `${count} recording${count !== 1 ? 's' : ''}`;
  }
}

function renderHistoryItems(items) {
  const historyList = document.getElementById('history-list');
  if (!historyList) return;
  
  if (items.length === 0) {
    historyList.innerHTML = `
      <div class="history-empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 15s1.5 2 4 2 4-2 4-2"/>
          <line x1="9" y1="9" x2="9.01" y2="9"/>
          <line x1="15" y1="9" x2="15.01" y2="9"/>
        </svg>
        <p>No recordings found</p>
        <span class="text-sm text-muted">Try adjusting your filters or record some audio!</span>
      </div>
    `;
    return;
  }
  
  let html = '';
  items.forEach(item => {
    const date = new Date(item.timestamp).toLocaleString();
    const size = item.size ? formatFileSize(item.size) : '';
    const hasResult = item.result && item.result.transcription;
    const status = hasResult ? 'completed' : (item.status || 'pending');
    const filename = item.originalFilename || item.filename || item.savedFilename || 'Recording';
    
    // Extract all result data
    const r = item.result || {};
    const transcription = r.transcription || '';
    const confidence = r.confidence || '';
    const sentiment = r.sentiment || '';
    const factCheck = r.fact_check || '';
    const brutalHonesty = r.brutal_honesty || '';
    const keywords = r.keywords || [];
    const processingTime = r.processing_time || '';
    const voiceAnalysis = r.voice_analysis || null;
    const sentenceMoods = r.sentence_moods || [];
    const agentsUsed = r.agents_used || ['Whisper STT', 'LLAMA Analysis'];
    const duration = voiceAnalysis?.duration_seconds ? Math.round(voiceAnalysis.duration_seconds) + 's' : '';
    
    // New fields for long recording analysis
    const summary = r.summary || '';
    const questionableClaims = r.questionable_claims || [];
    const corrections = r.corrections || [];
    const analysis = r.analysis || '';
    
    // Credibility score from analysis
    const credScore = r.credibility_score || (confidence ? Math.round(parseFloat(confidence) * 100) : null);
    const credClass = credScore >= 70 ? 'cred-success' : credScore >= 40 ? 'cred-warning' : 'cred-error';
    
    html += `
      <div class="history-card" data-id="${item.id}" data-status="${status}" data-sentiment="${sentiment}">
        <!-- Header Block -->
        <div class="history-block header-block">
          <div class="history-header">
            <div class="history-title">
              <span class="history-filename">${escapeHtml(filename)}</span>
              <span class="status-pill ${status}">${status}</span>
            </div>
            <div class="history-actions-inline">
              <button class="btn btn-secondary btn-sm" onclick="downloadHistoryItem('${item.id}')" title="Download">
                <i data-lucide="download" style="width: 14px; height: 14px;"></i>
              </button>
              ${!hasResult ? `<button class="btn btn-primary btn-sm" onclick="reanalyzeHistoryItem('${item.id}')">Re-analyze</button>` : ''}
              <button class="btn btn-danger btn-sm" onclick="deleteHistoryItem('${item.id}')" title="Delete">
                <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
              </button>
            </div>
          </div>
          <div class="history-meta-row">
            <span class="meta-item">${date}</span>
            ${duration ? `<span class="meta-item">${duration}</span>` : ''}
            ${size ? `<span class="meta-item">${size}</span>` : ''}
            ${sentiment ? `<span class="meta-item sentiment-${sentiment}">${sentiment}</span>` : ''}
            ${processingTime ? `<span class="meta-item">${processingTime}</span>` : ''}
          </div>
          ${credScore !== null ? `
            <div class="cred-bar-mini">
              <div class="cred-bar-mini-fill ${credClass}" style="width: ${credScore}%"></div>
            </div>
            <div class="cred-label">Cred: ${credScore}%</div>
          ` : ''}
        </div>
        
        ${summary ? `
          <!-- Summary Block (for long recordings) -->
          <div class="history-block summary-block">
            <div class="block-title">📝 Summary</div>
            <div class="summary-text">${escapeHtml(summary)}</div>
          </div>
        ` : ''}
        
        ${transcription ? `
          <!-- Transcription Block -->
          <div class="history-block transcription-block">
            <div class="block-title" style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="toggleSection(this)">
              <span>📄 Full Transcription ${transcription.length > 500 ? `(${transcription.length} chars)` : ''}</span>
              <span class="toggle-icon">${transcription.length > 500 ? '▶' : '▼'}</span>
            </div>
            <div class="transcription-text" style="${transcription.length > 500 ? 'display: none;' : ''}">${formatTranscriptionWithMoods(transcription, sentenceMoods)}</div>
          </div>
        ` : `
          <div class="history-block">
            <div class="no-transcription">No transcription</div>
          </div>
        `}
        
        <!-- Analysis badges row -->
        <div class="history-block badges-block">
          <div class="recording-badges">
            ${sentiment ? `<span class="badge badge-${getSentimentClass(sentiment)}">${sentiment}</span>` : ''}
            ${confidence ? `<span class="badge badge-neutral">Conf: ${typeof confidence === 'number' ? Math.round(confidence * 100) + '%' : confidence}</span>` : ''}
            ${processingTime ? `<span class="badge badge-neutral">Time: ${processingTime}</span>` : ''}
          </div>
        </div>
        
        ${questionableClaims.length > 0 || corrections.length > 0 ? `
          <!-- Mistakes / Unfacts Block -->
          <div class="history-block mistakes-block">
            <div class="block-title mistakes-title">
              <span>❌ Mistakes & Questionable Claims (${questionableClaims.length + corrections.length})</span>
            </div>
            <div class="mistakes-content">
              ${questionableClaims.map(claim => `
                <div class="mistake-item">
                  <span class="mistake-icon">⚠️</span>
                  <span class="mistake-text">${escapeHtml(typeof claim === 'string' ? claim : claim.text || claim.claim || JSON.stringify(claim))}</span>
                </div>
              `).join('')}
              ${corrections.map(correction => `
                <div class="correction-item">
                  <span class="correction-icon">✏️</span>
                  <span class="correction-text">${escapeHtml(typeof correction === 'string' ? correction : correction.text || correction.correction || JSON.stringify(correction))}</span>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
        
        ${brutalHonesty || factCheck ? `
          <!-- Fact Check / Analysis Block -->
          <div class="history-block analysis-block">
            <div class="block-title" style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="toggleSection(this)">
              <span>🔍 Detailed Fact Analysis</span>
              <span class="toggle-icon">▶</span>
            </div>
            <div class="analysis-content" style="display: none;">
              ${brutalHonesty ? `
                <div class="analysis-section">
                  <div class="analysis-label">Brutal Honest Assessment:</div>
                  <div class="brutal-honesty-content">${formatBrutalHonesty(brutalHonesty)}</div>
                </div>
              ` : ''}
              ${factCheck ? `
                <div class="analysis-section">
                  <div class="analysis-label">Fact Check:</div>
                  <div class="fact-check-content">${escapeHtml(factCheck)}</div>
                </div>
              ` : ''}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  });
  
  historyList.innerHTML = html;
  
  // Reinitialize Lucide icons for the new content
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

function getSentimentClass(sentiment) {
  const s = (sentiment || '').toLowerCase();
  if (s === 'positive') return 'success';
  if (s === 'negative') return 'error';
  return 'neutral';
}

async function downloadHistoryItem(id) {
  try {
    const response = await fetch(`/api/transcription-history/${id}/download`);
    if (response.ok) {
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recording-${id}.wav`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      if (window.showNotification) window.showNotification('error', 'Download not available');
    }
  } catch (error) {
    if (window.showNotification) window.showNotification('error', 'Failed to download');
  }
}

async function reanalyzeHistoryItem(id) {
  if (window.showNotification) window.showNotification('info', 'Re-analyzing recording...');
  try {
    const response = await fetch(`/api/transcription-history/${id}/reanalyze`, { method: 'POST' });
    if (response.ok) {
      if (window.showNotification) window.showNotification('success', 'Re-analysis complete');
      loadTranscriptionHistory();
    }
  } catch (error) {
    if (window.showNotification) window.showNotification('error', 'Re-analysis failed');
  }
}

function formatTranscriptionWithMoods(text, moods) {
  if (!text) return '';
  if (!moods || moods.length === 0) {
    return escapeHtml(text);
  }
  
  // Split into sentences and apply mood tags
  const sentences = text.split(/(?<=[.!?])\s+/);
  let html = '';
  
  sentences.forEach((sentence, i) => {
    const mood = moods[i] || { mood: 'neutral', confidence: 0.5 };
    const moodClass = `mood-${mood.mood || 'neutral'}`;
    const moodIcon = getMoodIcon(mood.mood);
    html += `<span class="sentence ${moodClass}" title="${mood.mood} (${Math.round((mood.confidence || 0.5) * 100)}%)">${moodIcon} ${escapeHtml(sentence)} </span>`;
  });
  
  return html;
}

function getMoodIcon(mood) {
  const icons = {
    happy: '<span class="mood-icon happy">:)</span>',
    sad: '<span class="mood-icon sad">:(</span>',
    angry: '<span class="mood-icon angry">>:(</span>',
    anxious: '<span class="mood-icon anxious">:/</span>',
    confident: '<span class="mood-icon confident">B)</span>',
    uncertain: '<span class="mood-icon uncertain">?</span>',
    neutral: '',
    frustrated: '<span class="mood-icon frustrated">X(</span>',
    excited: '<span class="mood-icon excited">:D</span>',
  };
  return icons[mood] || '';
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function getIndicatorColor(value) {
  // Green for high, yellow for medium, red for low
  if (value >= 0.7) return '#22c55e';
  if (value >= 0.4) return '#f59e0b';
  return '#ef4444';
}

function getStressColor(value) {
  // Inverse: green for low stress, red for high stress
  if (value <= 0.3) return '#22c55e';
  if (value <= 0.6) return '#f59e0b';
  return '#ef4444';
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatBrutalHonesty(text) {
  if (!text) return '';
  // Parse the claim analysis format: VERIFIED|claim|reasoning
  const lines = text.split('\n');
  let html = '';
  
  lines.forEach(line => {
    if (line.includes('|')) {
      const parts = line.split('|');
      if (parts.length >= 3) {
        const status = parts[0].trim();
        const claim = parts[1].trim();
        const reasoning = parts[2].trim();
        
        let statusClass = 'claim-neutral';
        let statusIcon = '?';
        if (status === 'VERIFIED') {
          statusClass = 'claim-verified';
          statusIcon = '✓';
        } else if (status === 'INCORRECT') {
          statusClass = 'claim-incorrect';
          statusIcon = '✗';
        } else if (status === 'NUANCED') {
          statusClass = 'claim-nuanced';
          statusIcon = '~';
        }
        
        html += `
          <div class="claim-item ${statusClass}">
            <div class="claim-status">${statusIcon} ${status}</div>
            <div class="claim-text">"${escapeHtml(claim)}"</div>
            <div class="claim-reasoning">${escapeHtml(reasoning)}</div>
          </div>
        `;
      }
    } else if (line.trim()) {
      html += `<div class="analysis-line">${escapeHtml(line)}</div>`;
    }
  });
  
  return html || escapeHtml(text);
}

async function deleteHistoryItem(id) {
  if (!confirm('Delete this recording?')) return;
  
  try {
    const response = await fetch(`/api/transcription-history/${id}`, { method: 'DELETE' });
    if (response.ok) {
      if (window.showNotification) window.showNotification('success', 'Recording deleted');
      loadTranscriptionHistory();
    }
  } catch (error) {
    if (window.showNotification) window.showNotification('error', 'Failed to delete recording');
  }
}

async function transcribeHistoryItem(id) {
  if (window.showNotification) window.showNotification('info', 'Starting transcription...');
  // TODO: Implement transcription of history item
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Initialize tab from URL hash
  const hash = window.location.hash.slice(1);
  if (hash && ['record', 'upload', 'history', 'device'].includes(hash)) {
    switchTab(hash);
  } else {
    switchTab('record');
  }
  
  // Load history
  loadTranscriptionHistory();
  
  // Reinitialize Lucide icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
});

// Handle hash changes
window.addEventListener('hashchange', () => {
  const hash = window.location.hash.slice(1);
  if (hash && ['record', 'upload', 'history', 'device'].includes(hash)) {
    switchTab(hash);
  }
});

// Toggle any collapsible section visibility
function toggleSection(element) {
  const parent = element.parentElement;
  const content = parent.querySelector('.analysis-content, .transcription-text, .summary-text');
  const icon = element.querySelector('.toggle-icon');
  if (content) {
    if (content.style.display === 'none') {
      content.style.display = 'block';
      icon.textContent = '▼';
    } else {
      content.style.display = 'none';
      icon.textContent = '▶';
    }
  }
}

// Legacy alias
function toggleAnalysis(element) {
  toggleSection(element);
}

// Make functions globally available
window.switchTab = switchTab;
window.loadTranscriptionHistory = loadTranscriptionHistory;
window.filterHistory = filterHistory;
window.deleteHistoryItem = deleteHistoryItem;
window.transcribeHistoryItem = transcribeHistoryItem;
window.updateRecordingUI = updateRecordingUI;
window.loadHistory = loadTranscriptionHistory;
window.downloadHistoryItem = downloadHistoryItem;
window.reanalyzeHistoryItem = reanalyzeHistoryItem;
window.toggleAnalysis = toggleAnalysis;
window.toggleSection = toggleSection;

console.log('Home.js loaded');
