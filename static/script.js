// Utility functions for GST Tracker App

const API_BASE_URL = '/api';

function formatRupee(amount) {
    if(amount === undefined || amount === null) return '₹0.00';
    return '₹' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function checkAuth(requireAuth = true) {
    const userId = localStorage.getItem('gst_user_id');
    const path = window.location.pathname;

    if (requireAuth && !userId) {
        if (path !== '/') {
            window.location.href = '/';
        }
    } else if (!requireAuth && userId) {
        if (path === '/') {
            window.location.href = '/dashboard';
        }
    }
    return userId;
}

function logout() {
    localStorage.removeItem('gst_user_id');
    localStorage.removeItem('gst_user_name');
    localStorage.removeItem('gst_business_name');
    window.location.href = '/';
}

function getUserId() {
    return localStorage.getItem('gst_user_id');
}

// Ensure mobile sidebar toggle works
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.querySelector('.mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Set active nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-item');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Attach logout event
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});
