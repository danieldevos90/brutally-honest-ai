// Profiles Page JavaScript
let currentProfileType = 'clients';

function switchProfileType(type) {
    currentProfileType = type;
    
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(function(btn) {
        btn.classList.remove('active');
    });
    var activeTab = document.getElementById('tab-' + type);
    if (activeTab) activeTab.classList.add('active');
    
    // Show/hide fields
    var personFields = document.getElementById('person-fields');
    var personCompanyField = document.getElementById('person-company-field');
    var brandValuesField = document.getElementById('brand-values-field');
    
    if (personFields) personFields.style.display = 'none';
    if (personCompanyField) personCompanyField.style.display = 'none';
    if (brandValuesField) brandValuesField.style.display = 'none';
    
    if (type === 'clients') {
        document.getElementById('create-profile-title').textContent = 'Create Client Profile';
        document.getElementById('profiles-list-title').textContent = 'Client Profiles';
    } else if (type === 'brands') {
        if (brandValuesField) brandValuesField.style.display = 'flex';
        document.getElementById('create-profile-title').textContent = 'Create Brand Profile';
        document.getElementById('profiles-list-title').textContent = 'Brand Profiles';
    } else if (type === 'persons') {
        if (personFields) personFields.style.display = 'flex';
        if (personCompanyField) personCompanyField.style.display = 'flex';
        document.getElementById('create-profile-title').textContent = 'Create Person Profile';
        document.getElementById('profiles-list-title').textContent = 'Person Profiles';
    }
    
    loadProfiles();
    var form = document.getElementById('create-profile-form');
    if (form) form.reset();
}

async function createProfile(event) {
    event.preventDefault();
    
    try {
        var name = document.getElementById('profile-name').value;
        var description = document.getElementById('profile-description').value;
        var tags = document.getElementById('profile-tags').value;
        
        var formData = new URLSearchParams();
        formData.append('name', name);
        formData.append('description', description);
        if (tags) formData.append('tags', tags);
        
        var endpoint = '';
        if (currentProfileType === 'clients') {
            endpoint = '/api/profiles/clients';
        } else if (currentProfileType === 'brands') {
            var values = document.getElementById('profile-values').value;
            if (values) formData.append('values', values);
            endpoint = '/api/profiles/brands';
        } else if (currentProfileType === 'persons') {
            var role = document.getElementById('profile-role').value;
            var company = document.getElementById('profile-company').value;
            if (role) formData.append('role', role);
            if (company) formData.append('company', company);
            endpoint = '/api/profiles/persons';
        }
        
        var response = await fetch(endpoint + '?' + formData.toString(), { method: 'POST' });
        var result = await response.json();
        
        if (result.success) {
            if (typeof showNotification === 'function') {
                showNotification('success', 'Profile created successfully!');
            } else {
                alert('Profile created successfully!');
            }
            document.getElementById('create-profile-form').reset();
            loadProfiles();
        } else {
            if (typeof showNotification === 'function') {
                showNotification('error', result.error || 'Failed to create profile');
            } else {
                alert('Failed to create profile');
            }
        }
    } catch (error) {
        console.error('Error creating profile:', error);
        if (typeof showNotification === 'function') {
            showNotification('error', 'Error creating profile');
        } else {
            alert('Error creating profile');
        }
    }
}

async function loadProfiles() {
    try {
        var endpoint = '/api/profiles/' + currentProfileType;
        var response = await fetch(endpoint);
        var result = await response.json();
        
        var listEl = document.getElementById('profiles-list');
        if (!listEl) return;
        
        if (result.success && result.profiles && result.profiles.length > 0) {
            listEl.innerHTML = result.profiles.map(function(profile) {
                return '<div class="profile-card">' +
                    '<div class="profile-header">' +
                    '<div class="profile-info">' +
                    '<span class="profile-name">' + escapeHtml(profile.name) + '</span>' +
                    (profile.type ? '<span class="profile-badge">' + escapeHtml(profile.type) + '</span>' : '') +
                    (profile.role ? '<span class="profile-badge">' + escapeHtml(profile.role) + '</span>' : '') +
                    '</div>' +
                    '<button onclick="deleteProfile(\'' + profile.id + '\')" class="btn btn-tertiary btn-sm">Delete</button>' +
                    '</div>' +
                    '<p class="profile-description">' + escapeHtml(profile.description) + '</p>' +
                    (profile.tags && profile.tags.length > 0 ? 
                        '<div class="profile-tags">' + profile.tags.map(function(tag) { 
                            return '<span class="profile-tag">' + escapeHtml(tag) + '</span>'; 
                        }).join('') + '</div>' : '') +
                    '<div class="profile-footer">' +
                    '<span class="profile-facts">' + (profile.facts ? profile.facts.length : 0) + ' facts</span>' +
                    '<button onclick="viewProfile(\'' + profile.id + '\')" class="btn btn-secondary btn-sm">View Details</button>' +
                    '</div>' +
                    '</div>';
            }).join('');
        } else {
            listEl.innerHTML = '<div class="text-center text-muted p-4">No profiles yet. Create your first profile above.</div>';
        }
    } catch (error) {
        console.error('Error loading profiles:', error);
        var listEl = document.getElementById('profiles-list');
        if (listEl) {
            listEl.innerHTML = '<div class="text-center text-muted p-4">Error loading profiles. Please try again.</div>';
        }
    }
}

async function deleteProfile(profileId) {
    if (!confirm('Delete this profile?')) return;
    
    try {
        var endpoint = '/api/profiles/' + currentProfileType + '/' + profileId;
        var response = await fetch(endpoint, { method: 'DELETE' });
        var result = await response.json();
        
        if (result.success) {
            if (typeof showNotification === 'function') {
                showNotification('success', 'Profile deleted');
            }
            loadProfiles();
        } else {
            if (typeof showNotification === 'function') {
                showNotification('error', 'Failed to delete profile');
            } else {
                alert('Failed to delete profile');
            }
        }
    } catch (error) {
        console.error('Error deleting profile:', error);
        if (typeof showNotification === 'function') {
            showNotification('error', 'Error deleting profile');
        } else {
            alert('Error deleting profile');
        }
    }
}

function viewProfile(profileId) {
    alert('Profile details view coming soon! ID: ' + profileId);
}

function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally available
window.switchProfileType = switchProfileType;
window.createProfile = createProfile;
window.loadProfiles = loadProfiles;
window.deleteProfile = deleteProfile;
window.viewProfile = viewProfile;

// Initialize on load
document.addEventListener('DOMContentLoaded', function() {
    loadProfiles();
});

console.log('Profiles.js loaded');
