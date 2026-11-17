/**
 * scriptdash.js - Dashboard client logic for FINDR.
 * Handles session validation, user profile fetching, role-based adjustments, and logout.
 */

document.addEventListener('DOMContentLoaded', async () => {
    const logoutBtn = document.getElementById('logout-btn');
    const sidebarLogoutBtn = document.getElementById('sidebar-logout-btn');

    // ==========================================
    // 1. Verify Authentication & Load Profile
    // ==========================================

    let currentUser = null;

    try {
        const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
        if (!response.ok) {
            // Not authenticated -> redirect to login
            window.location.href = '/';
            return;
        }

        const data = await response.json();
        currentUser = data.user;
        console.log('Logged in as:', currentUser.username, `(${currentUser.role})`);

    } catch (err) {
        console.error('Failed to authenticate session:', err);
        window.location.href = '/';
        return;
    }

    // ==========================================
    // 2. Handle Logout
    // ==========================================

    async function handleLogout(e) {
        if (e) e.preventDefault();
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'same-origin'
            });
        } catch (err) {
            console.error('Logout error:', err);
        } finally {
            window.location.href = '/';
        }
    }

    if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
    if (sidebarLogoutBtn) sidebarLogoutBtn.addEventListener('click', handleLogout);
});
