// Authentication helper functions for FastAPI frontend
const API_BASE_URL = 'http://localhost:8000';

// Check if user is authenticated and update UI accordingly
async function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        showUnauthenticatedUI();
        return false;
    }
    
    try {
        // Verify token is valid by fetching user info
        const response = await fetch(`${API_BASE_URL}/users/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const user = await response.json();
            showAuthenticatedUI(user);
            return true;
        } else {
            // Token is invalid, remove it
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            showUnauthenticatedUI();
            return false;
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        showUnauthenticatedUI();
        return false;
    }
}

// Show UI for authenticated users
function showAuthenticatedUI(user) {
    // Hide auth buttons
    const authButtons = document.getElementById('auth-buttons');
    if (authButtons) {
        authButtons.style.display = 'none';
    }
    
    // Show user dropdown
    const userDropdown = document.getElementById('user-dropdown');
    if (userDropdown) {
        userDropdown.style.display = 'block';
    }
    
    // Update username display
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay) {
        usernameDisplay.textContent = user.username;
    }
    
    // Show authenticated navigation items
    const writeNav = document.getElementById('write-nav');
    const generateNav = document.getElementById('generate-nav');
    const actionButtons = document.getElementById('action-buttons');
    
    if (writeNav) writeNav.style.display = 'block';
    if (generateNav) generateNav.style.display = 'block';
    if (actionButtons) actionButtons.style.display = 'flex';
}

// Show UI for unauthenticated users
function showUnauthenticatedUI() {
    // Show auth buttons
    const authButtons = document.getElementById('auth-buttons');
    if (authButtons) {
        authButtons.style.display = 'flex';
    }
    
    // Hide user dropdown
    const userDropdown = document.getElementById('user-dropdown');
    if (userDropdown) {
        userDropdown.style.display = 'none';
    }
    
    // Hide authenticated navigation items
    const writeNav = document.getElementById('write-nav');
    const generateNav = document.getElementById('generate-nav');
    const actionButtons = document.getElementById('action-buttons');
    
    if (writeNav) writeNav.style.display = 'none';
    if (generateNav) generateNav.style.display = 'none';
    if (actionButtons) actionButtons.style.display = 'none';
}

// Logout function
async function logout() {
    try {
        const token = localStorage.getItem('access_token');
        
        // Call logout endpoint if available
        if (token) {
            await fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        }
    } catch (error) {
        console.error('Error during logout:', error);
    } finally {
        // Clear local storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        
        // Redirect to home page
        window.location.href = '/';
    }
}

// Get authorization headers for API calls
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        return {};
    }
    
    return {
        'Authorization': `Bearer ${token}`
    };
}

// Check if user is authenticated (simple boolean check)
function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Handle API errors (especially authentication errors)
function handleApiError(response) {
    if (response.status === 401) {
        // Unauthorized - token might be expired
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        window.location.href = '/login';
        return;
    }
    
    // Handle other errors as needed
    throw new Error(`API Error: ${response.status}`);
}

// Make authenticated API request
async function authenticatedFetch(url, options = {}) {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        window.location.href = '/login';
        return;
    }
    
    return response;
}

// Initialize authentication check on page load
document.addEventListener('DOMContentLoaded', function() {
    // Only check auth status if checkAuthStatus function hasn't been called yet
    if (typeof window.authStatusChecked === 'undefined') {
        window.authStatusChecked = true;
        checkAuthStatus();
    }
});