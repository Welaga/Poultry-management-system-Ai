// Poultry Management System - Main JS

const API_BASE = '/api';

// ============ AUTH HELPERS ============
function getToken() {
    return localStorage.getItem('pms_token');
}

function setToken(token) {
    localStorage.setItem('pms_token', token);
}

function clearToken() {
    localStorage.removeItem('pms_token');
    localStorage.removeItem('pms_user');
}

function getUser() {
    const u = localStorage.getItem('pms_user');
    return u ? JSON.parse(u) : null;
}

function setUser(user) {
    localStorage.setItem('pms_user', JSON.stringify(user));
}

function logout() {
    clearToken();
    window.location.href = '/login';
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// ============ API CLIENT ============
async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method: options.method || 'GET',
        headers,
    };

    if (options.body) {
        config.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
    }

    try {
        const response = await fetch(API_BASE + endpoint, config);

        if (response.status === 401) {
            clearToken();
            window.location.href = '/login';
            return null;
        }

        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }
            return data;
        } else {
            return response;
        }
    } catch (err) {
        console.error('API error:', err);
        throw err;
    }
}

async function apiGet(endpoint) {
    return apiRequest(endpoint);
}

async function apiPost(endpoint, body) {
    return apiRequest(endpoint, { method: 'POST', body });
}

async function apiPut(endpoint, body) {
    return apiRequest(endpoint, { method: 'PUT', body });
}

async function apiDelete(endpoint) {
    return apiRequest(endpoint, { method: 'DELETE' });
}

// File upload
async function apiUpload(endpoint, formData) {
    const token = getToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(API_BASE + endpoint, {
        method: 'POST',
        headers,
        body: formData
    });
    if (response.status === 401) {
        clearToken();
        window.location.href = '/login';
        return null;
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Upload failed');
    return data;
}

// ============ UI HELPERS ============
function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container') || createAlertContainer();
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type}`;
    alertEl.textContent = message;
    container.appendChild(alertEl);
    setTimeout(() => alertEl.remove(), 4000);
}

function createAlertContainer() {
    const c = document.createElement('div');
    c.id = 'alert-container';
    c.style.position = 'fixed';
    c.style.top = '20px';
    c.style.right = '20px';
    c.style.zIndex = '9999';
    c.style.maxWidth = '400px';
    document.body.appendChild(c);
    return c;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDateOnly(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString();
}

function formatCurrency(n) {
    if (n === null || n === undefined) return '0.00';
    return Number(n).toFixed(2);
}

// ============ NAV / SIDEBAR ============
const NAV_ITEMS = [
    { key: 'dashboard', href: '/dashboard', icon: '📊', label: 'Dashboard' },
    { key: 'birds',     href: '/birds',     icon: '🐓', label: 'Birds' },
    { key: 'eggs',      href: '/eggs',      icon: '🥚', label: 'Eggs' },
    { key: 'feed',      href: '/feed',      icon: '🌾', label: 'Feed' },
    { key: 'health',    href: '/health',    icon: '💊', label: 'Health' },
    { key: 'camera',    href: '/camera',    icon: '📹', label: 'AI Camera' },
    { key: 'reports',   href: '/reports',   icon: '📄', label: 'Reports' },
    { key: 'files',     href: '/files',     icon: '📁', label: 'Files' },
    { key: 'chatbot',   href: '/chatbot',   icon: '🤖', label: 'Assistant' },
];

function renderSidebar(active = '') {
    const user = getUser() || { username: 'User', role: '' };
    const initial = (user.username || 'U').slice(0, 1).toUpperCase();

    const navHtml = NAV_ITEMS.map(item =>
        `<a href="${item.href}" class="${active === item.key ? 'active' : ''}">
            <span class="nav-icon">${item.icon}</span>
            <span>${item.label}</span>
        </a>`
    ).join('');

    return `
    <aside class="sidebar" id="sidebarEl">
        <div class="sidebar-brand">
            <div class="brand-icon">🐔</div>
            <div class="brand-name">Poultry MS</div>
        </div>
        <nav class="sidebar-nav">${navHtml}</nav>
        <div class="sidebar-footer">
            <div class="user-info">
                <div class="user-avatar">${initial}</div>
                <div class="user-meta">
                    <div class="user-name">${user.username}</div>
                    <div class="user-role">${user.role}</div>
                </div>
            </div>
            <button class="btn-logout" onclick="logout()">Sign out</button>
        </div>
    </aside>
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="closeMobileSidebar()"></div>
    `;
}

function openMobileSidebar() {
    document.getElementById('sidebarEl')?.classList.add('open');
    document.getElementById('sidebarOverlay')?.classList.add('show');
}
function closeMobileSidebar() {
    document.getElementById('sidebarEl')?.classList.remove('open');
    document.getElementById('sidebarOverlay')?.classList.remove('show');
}

// Initialize layout
function initLayout(activePage) {
    if (!requireAuth()) return;
    const sidebarEl = document.getElementById('sidebar');
    if (sidebarEl) sidebarEl.innerHTML = renderSidebar(activePage);
}
