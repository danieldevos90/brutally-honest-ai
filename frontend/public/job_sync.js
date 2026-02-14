/**
 * Job Sync - Cross-device job status synchronization
 * Shows active jobs for the logged-in user across all devices
 */

class JobSync {
    constructor() {
        this.activeJobs = [];
        this.isPolling = false;
        this.pollInterval = null;
        this.pollIntervalMs = 3000; // Poll every 3 seconds
        this.panelVisible = false;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        this.createUI();
        this.startPolling();
        console.log('[JobSync] Initialized - cross-device sync enabled');
    }
    
    createUI() {
        // Create the jobs panel container
        const panel = document.createElement('div');
        panel.id = 'active-jobs-panel';
        panel.className = 'active-jobs-panel';
        panel.innerHTML = `
            <div class="jobs-panel-header" onclick="jobSync.togglePanel()">
                <div class="jobs-panel-title">
                    <i data-lucide="activity" class="jobs-icon"></i>
                    <span>Active Jobs</span>
                    <span class="jobs-count" id="active-jobs-count">0</span>
                </div>
                <i data-lucide="chevron-down" class="jobs-chevron" id="jobs-chevron"></i>
            </div>
            <div class="jobs-panel-content" id="jobs-panel-content" style="display: none;">
                <div class="jobs-list" id="active-jobs-list">
                    <div class="jobs-empty">No active jobs</div>
                </div>
            </div>
        `;
        
        // Insert after connection-info panel
        const connectionInfo = document.getElementById('connection-info');
        if (connectionInfo) {
            connectionInfo.parentNode.insertBefore(panel, connectionInfo.nextSibling);
        } else {
            // Or insert after header
            const header = document.querySelector('.header');
            if (header) {
                header.parentNode.insertBefore(panel, header.nextSibling);
            }
        }
        
        // Reinitialize lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }
    
    togglePanel() {
        const content = document.getElementById('jobs-panel-content');
        const chevron = document.getElementById('jobs-chevron');
        
        if (content) {
            this.panelVisible = !this.panelVisible;
            content.style.display = this.panelVisible ? 'block' : 'none';
            
            if (chevron) {
                chevron.style.transform = this.panelVisible ? 'rotate(180deg)' : 'rotate(0)';
            }
        }
    }
    
    async fetchActiveJobs() {
        try {
            const response = await fetch('/api/user/jobs/active');
            if (!response.ok) {
                if (response.status === 401) {
                    // Not logged in, stop polling
                    this.stopPolling();
                    return [];
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return data.jobs || [];
        } catch (error) {
            console.error('[JobSync] Error fetching jobs:', error);
            return [];
        }
    }
    
    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        
        // Initial fetch
        this.updateJobs();
        
        // Set up interval
        this.pollInterval = setInterval(() => {
            this.updateJobs();
        }, this.pollIntervalMs);
        
        console.log('[JobSync] Started polling for active jobs');
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        this.isPolling = false;
        console.log('[JobSync] Stopped polling');
    }
    
    async updateJobs() {
        const jobs = await this.fetchActiveJobs();
        this.activeJobs = jobs;
        this.renderJobs();
        this.updateCount();
    }
    
    updateCount() {
        const countEl = document.getElementById('active-jobs-count');
        const panel = document.getElementById('active-jobs-panel');
        
        if (countEl) {
            countEl.textContent = this.activeJobs.length;
            countEl.style.display = this.activeJobs.length > 0 ? 'inline-flex' : 'none';
        }
        
        if (panel) {
            panel.classList.toggle('has-jobs', this.activeJobs.length > 0);
        }
    }
    
    renderJobs() {
        const listEl = document.getElementById('active-jobs-list');
        if (!listEl) return;
        
        if (this.activeJobs.length === 0) {
            listEl.innerHTML = '<div class="jobs-empty">No active jobs</div>';
            return;
        }
        
        listEl.innerHTML = this.activeJobs.map(job => this.renderJob(job)).join('');
        
        // Reinitialize icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }
    
    renderJob(job) {
        const statusIcon = this.getStatusIcon(job.status);
        const phaseText = this.getPhaseText(job.phase);
        const deviceInfo = job.device_name ? `<span class="job-device">${job.device_name}</span>` : '';
        
        return `
            <div class="job-item ${job.status}">
                <div class="job-header">
                    <i data-lucide="${statusIcon}" class="job-status-icon"></i>
                    <span class="job-filename" title="${job.filename}">${this.truncateFilename(job.filename)}</span>
                    ${deviceInfo}
                </div>
                <div class="job-progress">
                    <div class="job-progress-bar">
                        <div class="job-progress-fill" style="width: ${job.progress}%"></div>
                    </div>
                    <span class="job-progress-text">${job.progress}%</span>
                </div>
                <div class="job-phase">${phaseText}: ${job.progress_message || 'Processing...'}</div>
            </div>
        `;
    }
    
    getStatusIcon(status) {
        switch (status) {
            case 'pending': return 'clock';
            case 'uploading': return 'upload';
            case 'processing': return 'loader';
            case 'completed': return 'check-circle';
            case 'failed': return 'x-circle';
            default: return 'activity';
        }
    }
    
    getPhaseText(phase) {
        switch (phase) {
            case 'loading': return 'Loading';
            case 'transcribing': return 'Transcribing';
            case 'analyzing': return 'AI Analysis';
            case 'complete': return 'Complete';
            default: return 'Processing';
        }
    }
    
    truncateFilename(filename, maxLength = 25) {
        if (!filename) return 'Unknown';
        if (filename.length <= maxLength) return filename;
        
        const ext = filename.split('.').pop();
        const name = filename.slice(0, maxLength - ext.length - 4);
        return `${name}...${ext}`;
    }
    
    // Called when a new job is created locally
    notifyNewJob(jobId, filename) {
        console.log(`[JobSync] New local job: ${jobId} - ${filename}`);
        // Immediately update
        this.updateJobs();
        
        // Auto-expand panel when there are active jobs
        if (!this.panelVisible && this.activeJobs.length > 0) {
            this.togglePanel();
        }
    }
}

// Create global instance
window.jobSync = new JobSync();

// Add CSS styles dynamically
const jobSyncStyles = document.createElement('style');
jobSyncStyles.textContent = `
    .active-jobs-panel {
        background: var(--surface-color, #1e1e1e);
        border: 1px solid var(--border-color, #333);
        border-radius: 8px;
        margin: 8px 0;
        overflow: hidden;
        display: none;
    }
    
    .active-jobs-panel.has-jobs {
        display: block;
    }
    
    .jobs-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 16px;
        cursor: pointer;
        background: var(--surface-hover, #2a2a2a);
        transition: background 0.2s;
    }
    
    .jobs-panel-header:hover {
        background: var(--surface-active, #333);
    }
    
    .jobs-panel-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-primary, #fff);
    }
    
    .jobs-icon {
        width: 16px;
        height: 16px;
        color: var(--accent-color, #8b5cf6);
    }
    
    .jobs-count {
        background: var(--accent-color, #8b5cf6);
        color: white;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 10px;
        min-width: 20px;
        text-align: center;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    .jobs-chevron {
        width: 16px;
        height: 16px;
        color: var(--text-secondary, #888);
        transition: transform 0.2s;
    }
    
    .jobs-panel-content {
        padding: 12px 16px;
        border-top: 1px solid var(--border-color, #333);
    }
    
    .jobs-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .jobs-empty {
        text-align: center;
        color: var(--text-secondary, #888);
        font-size: 13px;
        padding: 12px;
    }
    
    .job-item {
        background: var(--surface-color, #1e1e1e);
        border: 1px solid var(--border-color, #333);
        border-radius: 6px;
        padding: 10px 12px;
    }
    
    .job-item.processing {
        border-color: var(--accent-color, #8b5cf6);
    }
    
    .job-item.pending {
        border-color: var(--warning-color, #f59e0b);
    }
    
    .job-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    
    .job-status-icon {
        width: 14px;
        height: 14px;
    }
    
    .job-item.processing .job-status-icon {
        color: var(--accent-color, #8b5cf6);
        animation: spin 1s linear infinite;
    }
    
    .job-item.pending .job-status-icon {
        color: var(--warning-color, #f59e0b);
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .job-filename {
        flex: 1;
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary, #fff);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .job-device {
        font-size: 11px;
        color: var(--text-secondary, #888);
        background: var(--surface-hover, #2a2a2a);
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    .job-progress {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    
    .job-progress-bar {
        flex: 1;
        height: 4px;
        background: var(--surface-hover, #2a2a2a);
        border-radius: 2px;
        overflow: hidden;
    }
    
    .job-progress-fill {
        height: 100%;
        background: var(--accent-color, #8b5cf6);
        border-radius: 2px;
        transition: width 0.3s ease;
    }
    
    .job-progress-text {
        font-size: 11px;
        color: var(--text-secondary, #888);
        min-width: 35px;
        text-align: right;
    }
    
    .job-phase {
        font-size: 11px;
        color: var(--text-secondary, #888);
    }
`;
document.head.appendChild(jobSyncStyles);
