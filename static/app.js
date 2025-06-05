// API endpoints
const API_BASE_URL = 'http://localhost:8000';

// Store recent submissions
let recentSubmissions = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Set up form submission handler
    const ingestForm = document.getElementById('ingestForm');
    ingestForm.addEventListener('submit', handleIngestSubmit);

    // Set up status check button handler
    const checkStatusButton = document.getElementById('checkStatusButton');
    checkStatusButton.addEventListener('click', checkStatus);
});

// Show loading state
function setLoading(elementId, isLoading) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (isLoading) {
        element.disabled = true;
        element.setAttribute('data-original-text', element.textContent);
        element.innerHTML = '<div class="spinner"></div> Loading...';
    } else {
        element.disabled = false;
        element.innerHTML = element.getAttribute('data-original-text') || element.textContent;
    }
}

// Handle form submission
async function handleIngestSubmit(event) {
    event.preventDefault();
    
    const submitButton = document.getElementById('submitButton');
    setLoading('submitButton', true);
    
    const idsInput = document.getElementById('ids').value;
    const priority = document.getElementById('priority').value;
    
    // Parse and validate IDs
    const ids = idsInput.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
    
    if (ids.length === 0) {
        showToast('Please enter valid IDs', 'error');
        setLoading('submitButton', false);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ids, priority }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to submit batch');
        }
        
        const data = await response.json();
        showToast('Batch submitted successfully!', 'success');
        
        // Add to recent submissions
        addRecentSubmission(data.ingestion_id, ids, priority);
        
        // Clear form
        document.getElementById('ids').value = '';
        
        // Auto-fill status checker
        document.getElementById('statusId').value = data.ingestion_id;
        
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        setLoading('submitButton', false);
    }
}

// Check status of an ingestion
async function checkStatus() {
    const checkButton = document.getElementById('checkStatusButton');
    setLoading('checkStatusButton', true);
    
    const ingestionId = document.getElementById('statusId').value.trim();
    
    if (!ingestionId) {
        showToast('Please enter an ingestion ID', 'error');
        setLoading('checkStatusButton', false);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/status/${ingestionId}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch status');
        }
        
        const data = await response.json();
        displayStatusResults(data);
        
    } catch (error) {
        showToast(error.message, 'error');
        document.getElementById('statusResults').classList.add('hidden');
    } finally {
        setLoading('checkStatusButton', false);
    }
}

// Display status results
function displayStatusResults(data) {
    const statusResults = document.getElementById('statusResults');
    const statusContent = document.getElementById('statusContent');
    
    // Create status display
    const statusHtml = `
        <div class="space-y-4 fade-in">
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Ingestion ID:</span>
                <span class="font-mono">${data.ingestion_id}</span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Overall Status:</span>
                <span class="status-badge status-${data.status.toLowerCase()}">${data.status}</span>
            </div>
            <div class="mt-4">
                <h3 class="text-lg font-medium text-gray-700 mb-2">Batches:</h3>
                <div class="space-y-2">
                    ${data.batches.map(batch => `
                        <div class="batch-card">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm text-gray-600">Batch ID:</span>
                                <span class="font-mono text-sm">${batch.batch_id}</span>
                            </div>
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm text-gray-600">Status:</span>
                                <span class="status-badge status-${batch.status.toLowerCase()}">${batch.status}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-sm text-gray-600">IDs:</span>
                                <span class="font-mono text-sm">${batch.ids.join(', ')}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    statusContent.innerHTML = statusHtml;
    statusResults.classList.remove('hidden');
}

// Add submission to recent submissions
function addRecentSubmission(ingestionId, ids, priority) {
    const submission = {
        ingestionId,
        ids,
        priority,
        timestamp: new Date().toISOString()
    };
    
    recentSubmissions.unshift(submission);
    if (recentSubmissions.length > 5) {
        recentSubmissions.pop();
    }
    
    updateRecentSubmissions();
}

// Update recent submissions display
function updateRecentSubmissions() {
    const container = document.getElementById('recentSubmissions');
    
    if (recentSubmissions.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center">No recent submissions</p>';
        return;
    }
    
    const html = recentSubmissions.map(sub => `
        <div class="batch-card fade-in">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm text-gray-600">ID:</span>
                <span class="font-mono text-sm">${sub.ingestionId}</span>
            </div>
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm text-gray-600">Priority:</span>
                <span class="status-badge status-${sub.priority.toLowerCase()}">${sub.priority}</span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">IDs:</span>
                <span class="font-mono text-sm">${sub.ids.join(', ')}</span>
            </div>
            <div class="mt-2 text-xs text-gray-500">
                ${new Date(sub.timestamp).toLocaleString()}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
} 