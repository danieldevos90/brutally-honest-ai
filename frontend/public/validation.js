// Validation page scripts
console.log('Validation.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Validation page DOM ready');
    loadKnowledgeBaseStats();
    
    // Add form submit handler
    var form = document.getElementById('validation-form');
    if (form) {
        console.log('Form found, adding submit listener');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted');
            validateText();
        });
    } else {
        console.error('Validation form not found!');
    }
    
    // Also add click handler to button as backup
    var btn = document.getElementById('validate-btn');
    if (btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Button clicked');
            validateText();
        });
    }
});

async function loadKnowledgeBaseStats() {
    try {
        var response = await fetch('/documents/stats');
        var result = await response.json();
        if (result.success) {
            document.getElementById('kb-documents').textContent = result.total_documents || 0;
        }
    } catch (e) {
        console.error('Error loading stats:', e);
    }
    try {
        var response = await fetch('/api/profiles/clients');
        var result = await response.json();
        if (result.success) {
            document.getElementById('kb-profiles').textContent = result.profiles ? result.profiles.length : 0;
        }
    } catch (e) {
        console.error('Error loading profiles:', e);
    }
}

async function validateText() {
    console.log('validateText called');
    var text = document.getElementById('test-text').value;
    console.log('Text to validate:', text);
    
    if (!text || !text.trim()) {
        alert('Please enter text to validate');
        return;
    }
    
    var resultsSection = document.getElementById('validation-results-section');
    var resultsDiv = document.getElementById('validation-results');
    
    resultsSection.style.display = 'block';
    resultsDiv.innerHTML = '<p class="text-center text-muted">Validating... This may take 10-30 seconds.</p>';
    
    try {
        console.log('Sending validation request...');
        var response = await fetch('/api/ai/validate_text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        console.log('Response status:', response.status);
        var result = await response.json();
        console.log('Validation result:', result);
        
        if (result.success && result.claims && result.claims.length > 0) {
            resultsDiv.innerHTML = result.claims.map(function(r) {
                var statusClass = r.status === 'confirmed' || r.status === 'verified' ? 'badge-success' : 
                                  (r.status === 'contradicted' || r.status === 'incorrect' ? 'badge-warning' : '');
                return '<div class="card" style="padding: 12px; margin-bottom: 8px;">' +
                    '<div class="flex justify-between items-center mb-2">' +
                    '<span class="text-sm font-medium">' + escapeHtml(r.claim || r.text || '') + '</span>' +
                    '<span class="badge ' + statusClass + '">' + (r.status || 'unverified') + '</span>' +
                    '</div>' +
                    '<p class="text-xs text-muted">' + escapeHtml(r.explanation || 'No explanation') + '</p>' +
                    '</div>';
            }).join('');
        } else if (result.error) {
            resultsDiv.innerHTML = '<p style="color: var(--color-danger);">Error: ' + escapeHtml(result.error) + '</p>';
        } else {
            resultsDiv.innerHTML = '<p class="text-muted">No claims found to validate.</p>';
        }
    } catch (error) {
        console.error('Validation error:', error);
        resultsDiv.innerHTML = '<p style="color: var(--color-danger);">Validation failed: ' + error.message + '</p>';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
