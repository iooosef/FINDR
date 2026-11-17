/**
 * scriptdash.js - Student Dashboard logic for FINDR.
 * Manages ticket listing, filtering, reporting lost items, info modal, notifications, and session.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // ==========================================
    // DOM Elements
    // ==========================================
    const userDisplayName = document.getElementById('user-display-name');
    const sidebarUserName = document.getElementById('sidebar-user-name');
    const sidebarUserRole = document.getElementById('sidebar-user-role');
    const logoutBtn = document.getElementById('logout-btn');
    const sidebarLogoutBtn = document.getElementById('sidebar-logout-btn');

    // Modals
    const lostModalOverlay = document.getElementById('lost-modal-overlay');
    const btnOpenLostModal = document.getElementById('btn-open-lost-modal');
    const btnQuickReport = document.getElementById('btn-quick-report');
    const closeLostModalBtn = document.getElementById('close-lost-modal-btn');
    const cancelLostBtn = document.getElementById('cancel-lost-btn');
    const lostItemForm = document.getElementById('lost-item-form');
    const submitLostBtn = document.getElementById('submit-lost-btn');
    const photoInput = document.getElementById('photo');
    const fileNamePreview = document.getElementById('file-name-preview');

    const foundInfoModalOverlay = document.getElementById('found-info-modal-overlay');
    const btnOpenFoundModal = document.getElementById('btn-open-found-modal');
    const closeFoundModalBtn = document.getElementById('close-found-modal-btn');
    const closeFoundInfoBtn = document.getElementById('close-found-info-btn');

    // Notifications
    const notifToggleBtn = document.getElementById('notif-toggle-btn');
    const mobileNotifBtn = document.getElementById('mobile-notif-btn');
    const notifDrawer = document.getElementById('notif-drawer');
    const notifOverlay = document.getElementById('notif-overlay');
    const closeNotifBtn = document.getElementById('close-notif-btn');
    const notifList = document.getElementById('notif-list');
    const notifBadge = document.getElementById('notif-badge');
    const mobileNotifBadge = document.getElementById('mobile-notif-badge');
    const markAllReadBtn = document.getElementById('mark-all-read-btn');

    // Tickets Grid & Filters
    const ticketsGrid = document.getElementById('tickets-grid');
    const filterTabs = document.querySelectorAll('.tab-btn');
    const countAll = document.getElementById('count-all');
    const countOpen = document.getElementById('count-open');
    const countMatched = document.getElementById('count-matched');
    const countResolved = document.getElementById('count-resolved');

    const toastContainer = document.getElementById('toast-container');

    let currentUser = null;
    let allTickets = [];
    let currentFilter = 'all';

    // ==========================================
    // 1. Toast Notification Helper
    // ==========================================

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = type === 'success' ? 'fa-circle-check' :
                     type === 'error' ? 'fa-circle-exclamation' : 'fa-bell';

        toast.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span>${message}</span>
        `;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(50px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ==========================================
    // 2. Authentication Check & Profile Loading
    // ==========================================

    try {
        const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
        if (!response.ok) {
            window.location.href = '/';
            return;
        }

        const data = await response.json();
        currentUser = data.user;

        // Display user info
        userDisplayName.textContent = currentUser.full_name.split(' ')[0] || currentUser.username;
        sidebarUserName.textContent = currentUser.full_name;
        sidebarUserRole.textContent = `${currentUser.role.toUpperCase()} (${currentUser.username})`;

    } catch (err) {
        console.error('Session check failed:', err);
        window.location.href = '/';
        return;
    }

    // ==========================================
    // 3. Load Student's Missing Tickets
    // ==========================================

    async function loadTickets() {
        try {
            const response = await fetch('/api/tickets/missing', { credentials: 'same-origin' });
            if (!response.ok) throw new Error('Failed to load tickets');

            const data = await response.json();
            allTickets = data.tickets || [];
            updateCounts();
            renderTickets();

        } catch (err) {
            console.error('Error fetching tickets:', err);
            ticketsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <p>Unable to load reports. Please try refreshing the page.</p>
                </div>
            `;
        }
    }

    function updateCounts() {
        const total = allTickets.length;
        const open = allTickets.filter(t => t.status === 'open').length;
        const matched = allTickets.filter(t => t.status === 'matched').length;
        const resolved = allTickets.filter(t => t.status === 'resolved').length;

        countAll.textContent = total;
        countOpen.textContent = open;
        countMatched.textContent = matched;
        countResolved.textContent = resolved;
    }

    function renderTickets() {
        const filtered = currentFilter === 'all'
            ? allTickets
            : allTickets.filter(t => t.status === currentFilter);

        if (filtered.length === 0) {
            ticketsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fa-regular fa-clipboard"></i>
                    <p>No ${currentFilter === 'all' ? '' : currentFilter} reports found.</p>
                    <button class="btn btn-yellow" style="margin-top: 14px;" onclick="document.getElementById('btn-open-lost-modal').click()">
                        Report a Missing Item
                    </button>
                </div>
            `;
            return;
        }

        ticketsGrid.innerHTML = filtered.map(ticket => {
            const statusClass = `status-${ticket.status}`;
            const statusLabel = ticket.status === 'open' ? 'Open' :
                                ticket.status === 'matched' ? 'Match Found' : 'Resolved';

            const photoHtml = ticket.photo_path
                ? `<img src="${ticket.photo_path}" alt="${ticket.item_name}" class="ticket-photo-thumb" loading="lazy">`
                : '';

            const matchCalloutHtml = ticket.status === 'matched'
                ? `
                <div class="match-alert-callout">
                    <i class="fa-solid fa-bell"></i>
                    <div>
                        <strong>Possible match found!</strong>
                        <p>Please visit the Lost & Found office at Balbago Building to verify ownership.</p>
                    </div>
                </div>
                `
                : '';

            return `
                <div class="ticket-card">
                    <div class="ticket-card-header">
                        <div>
                            <h4 class="ticket-item-name">${escapeHtml(ticket.item_name)}</h4>
                            <span class="ticket-category-tag">${escapeHtml(ticket.category)}</span>
                        </div>
                        <span class="status-badge ${statusClass}">${statusLabel}</span>
                    </div>

                    ${ticket.description ? `<p class="ticket-desc">${escapeHtml(ticket.description)}</p>` : ''}

                    <ul class="ticket-info-list">
                        <li>
                            <i class="fa-regular fa-calendar"></i>
                            <span>Lost: <strong>${escapeHtml(ticket.date_lost)}</strong> ${ticket.time_lost ? `(${escapeHtml(ticket.time_lost)})` : ''}</span>
                        </li>
                        <li>
                            <i class="fa-solid fa-location-dot"></i>
                            <span>Location: <strong>${escapeHtml(ticket.locations)}</strong></span>
                        </li>
                        ${ticket.color || ticket.brand ? `
                        <li>
                            <i class="fa-solid fa-tag"></i>
                            <span>${ticket.brand ? `Brand: <strong>${escapeHtml(ticket.brand)}</strong> ` : ''}${ticket.color ? `Color: <strong>${escapeHtml(ticket.color)}</strong>` : ''}</span>
                        </li>
                        ` : ''}
                    </ul>

                    ${photoHtml}
                    ${matchCalloutHtml}

                    <div class="ticket-footer">
                        <span>Report #${ticket.id}</span>
                        <span>Filed: ${formatDate(ticket.created_at)}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Filter tab switching
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentFilter = tab.getAttribute('data-filter');
            renderTickets();
        });
    });

    // ==========================================
    // 4. Lost Something? Modal Handling
    // ==========================================

    function openLostModal() {
        lostModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        document.getElementById('date-lost').value = new Date().toISOString().split('T')[0];
    }

    function closeLostModal() {
        lostModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        lostItemForm.reset();
        fileNamePreview.textContent = '';
    }

    if (btnOpenLostModal) btnOpenLostModal.addEventListener('click', openLostModal);
    if (btnQuickReport) btnQuickReport.addEventListener('click', openLostModal);
    if (closeLostModalBtn) closeLostModalBtn.addEventListener('click', closeLostModal);
    if (cancelLostBtn) cancelLostBtn.addEventListener('click', closeLostModal);

    lostModalOverlay.addEventListener('click', (e) => {
        if (e.target === lostModalOverlay) closeLostModal();
    });

    // Photo input change preview
    photoInput.addEventListener('change', () => {
        if (photoInput.files.length > 0) {
            const file = photoInput.files[0];
            if (file.size > 5 * 1024 * 1024) {
                showToast('File size exceeds 5 MB limit.', 'error');
                photoInput.value = '';
                fileNamePreview.textContent = '';
                return;
            }
            fileNamePreview.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        } else {
            fileNamePreview.textContent = '';
        }
    });

    // Form submit
    lostItemForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtnText = submitLostBtn.innerHTML;
        submitLostBtn.disabled = true;
        submitLostBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';

        try {
            const formData = new FormData(lostItemForm);

            const res = await fetch('/api/tickets/missing', {
                method: 'POST',
                credentials: 'same-origin',
                body: formData
            });

            const data = await res.json();

            if (res.ok) {
                closeLostModal();
                if (data.matches_found > 0) {
                    showToast(`Report filed! ${data.matches_found} potential match found. Check your notifications!`, 'success');
                } else {
                    showToast('Missing ticket submitted successfully.', 'success');
                }
                await loadTickets();
                await loadNotifications();
            } else {
                showToast(data.detail || 'Failed to submit report.', 'error');
            }
        } catch (err) {
            console.error('Error submitting lost report:', err);
            showToast('Network error. Please try again.', 'error');
        } finally {
            submitLostBtn.disabled = false;
            submitLostBtn.innerHTML = submitBtnText;
        }
    });

    // ==========================================
    // 5. Found Something? Student Info Modal
    // ==========================================

    function openFoundInfoModal() {
        foundInfoModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeFoundInfoModal() {
        foundInfoModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (btnOpenFoundModal) btnOpenFoundModal.addEventListener('click', openFoundInfoModal);
    if (closeFoundModalBtn) closeFoundModalBtn.addEventListener('click', closeFoundInfoModal);
    if (closeFoundInfoBtn) closeFoundInfoBtn.addEventListener('click', closeFoundInfoModal);

    foundInfoModalOverlay.addEventListener('click', (e) => {
        if (e.target === foundInfoModalOverlay) closeFoundInfoModal();
    });

    // ==========================================
    // 6. Notifications Drawer & Management
    // ==========================================

    function openNotifDrawer() {
        notifDrawer.classList.add('active');
        notifOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeNotifDrawer() {
        notifDrawer.classList.remove('active');
        notifOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (notifToggleBtn) notifToggleBtn.addEventListener('click', openNotifDrawer);
    if (mobileNotifBtn) mobileNotifBtn.addEventListener('click', openNotifDrawer);
    if (closeNotifBtn) closeNotifBtn.addEventListener('click', closeNotifDrawer);
    if (notifOverlay) notifOverlay.addEventListener('click', closeNotifDrawer);

    async function loadNotifications() {
        try {
            const res = await fetch('/api/notifications', { credentials: 'same-origin' });
            if (!res.ok) return;

            const data = await res.json();
            const unreadCount = data.unread_count || 0;
            const notifs = data.notifications || [];

            // Update badge indicators
            if (unreadCount > 0) {
                notifBadge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                notifBadge.style.display = 'flex';
                mobileNotifBadge.textContent = unreadCount;
                mobileNotifBadge.style.display = 'flex';
            } else {
                notifBadge.style.display = 'none';
                mobileNotifBadge.style.display = 'none';
            }

            if (notifs.length === 0) {
                notifList.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-regular fa-bell-slash"></i>
                        <p>No notifications yet</p>
                    </div>
                `;
                return;
            }

            notifList.innerHTML = notifs.map(n => `
                <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
                    <p>${escapeHtml(n.message)}</p>
                    <span class="notif-time">${formatDate(n.created_at)}</span>
                </div>
            `).join('');

            // Click single notification to mark as read
            document.querySelectorAll('.notif-item.unread').forEach(item => {
                item.addEventListener('click', async () => {
                    const id = item.getAttribute('data-id');
                    try {
                        await fetch(`/api/notifications/${id}/read`, {
                            method: 'PUT',
                            credentials: 'same-origin'
                        });
                        item.classList.remove('unread');
                        loadNotifications();
                    } catch (e) {
                        console.error('Error marking notif read:', e);
                    }
                });
            });

        } catch (err) {
            console.error('Error loading notifications:', err);
        }
    }

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/notifications/read-all', {
                    method: 'PUT',
                    credentials: 'same-origin'
                });
                if (res.ok) {
                    showToast('All notifications marked as read', 'info');
                    loadNotifications();
                }
            } catch (err) {
                console.error('Mark all read error:', err);
            }
        });
    }

    // ==========================================
    // 7. Logout Handling
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

    // ==========================================
    // 8. Utility Functions
    // ==========================================

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, m => map[m]);
    }

    function formatDate(isoString) {
        if (!isoString) return '';
        try {
            const d = new Date(isoString);
            return d.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
        } catch {
            return isoString;
        }
    }

    // Initial data fetch
    await loadTickets();
    await loadNotifications();
});
