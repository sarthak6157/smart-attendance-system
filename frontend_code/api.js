// 1. Core Configuration - This fixes the "not defined" error
const LIVE_BACKEND_URL = "https://smart-attendance-api-2dol.onrender.com/api";

const API_CONFIG = {
    BASE_URL: LIVE_BACKEND_URL
};

// 2. Session Management Helpers
const auth = {
    // Get the saved token
    getToken: () => localStorage.getItem('token'),
    
    // Check if user is logged in
    isAuthenticated: () => !!localStorage.getItem('token'),
    
    // Clear session on logout
    logout: () => {
        localStorage.clear();
        window.location.href = 'login_page.html';
    },

    // Get current user details
    getUser: () => ({
        name: localStorage.getItem('user_name'),
        role: localStorage.getItem('user_role'),
        id: localStorage.getItem('user_id')
    })
};

// 3. Global Guard Function
// This prevents students from accessing admin pages and vice versa
function checkAccess(requiredRole) {
    const user = auth.getUser();
    if (!auth.isAuthenticated()) {
        window.location.href = 'login_page.html';
        return;
    }
    if (requiredRole && user.role !== requiredRole) {
        alert("Access Denied: You do not have permission for this page.");
        window.location.href = 'login_page.html';
    }
}

// Ensure the variable is available globally for login_page.html
window.LIVE_BACKEND_URL = LIVE_BACKEND_URL;
