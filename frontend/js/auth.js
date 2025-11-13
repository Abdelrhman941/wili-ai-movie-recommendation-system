const API_URL = 'http://127.0.0.1:5000/api';

// Sign up function
async function signup(username, password) {
    const response = await fetch(`${API_URL}/auth/signup`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || 'Signup failed');
    }
    
    // Store token and user info
    localStorage.setItem('token', data.token);
    localStorage.setItem('user_id', data.user_id);
    localStorage.setItem('username', data.username);
    
    return data;
}

// Login function
async function login(username, password) {
    const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || 'Login failed');
    }
    
    // Store token and user info
    localStorage.setItem('token', data.token);
    localStorage.setItem('user_id', data.user_id);
    localStorage.setItem('username', data.username);
    localStorage.setItem('has_embedding', data.has_embedding);
    
    return data;
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('has_embedding');
    window.location.href = 'index.html';
}

// Check if user is authenticated
function isAuthenticated() {
    return localStorage.getItem('token') !== null;
}

// Get auth headers
function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    };
}

// Verify token
async function verifyToken() {
    if (!isAuthenticated()) {
        return false;
    }
    
    try {
        const response = await fetch(`${API_URL}/auth/verify`, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Protect page (redirect to login if not authenticated)
async function protectPage() {
    const authenticated = await verifyToken();
    if (!authenticated) {
        window.location.href = 'login.html';
    }
}