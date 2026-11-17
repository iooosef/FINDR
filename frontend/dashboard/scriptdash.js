/**
 * scriptdash.js - Comprehensive Dashboard logic for FINDR.
 * Supports both Student and Staff experiences dynamically based on authenticated role.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // ==========================================
    // DOM Elements - Navigation & User Profile
    // ==========================================
    const userDisplayName = document.getElementById('user-display-name');
    const userRoleIcon = document.getElementById('user-role-icon');
    const sidebarUserName = document.getElementById('sidebar-user-name');
    const sidebarUserRole = document.getElementById('sidebar-user-role');
    const logoutBtn = document.getElementById('logout-btn');
    const sidebarLogoutBtn = document.getElementById('sidebar-logout-btn');

    const navMainLink = document.getElementById('nav-main-link');
    const sidebarMainLink = document.getElementById('sidebar-main-link');
    const heroActionLink = document.getElementById('hero-action-link');

    // Role Sections
    const studentSection = document.getElementById('student-section');
    const staffSection = document.getElementById('staff-section');

    // Hero Buttons
    const btnOpenLostModal = document.getElementById('btn-open-lost-modal');
    const btnOpenFoundModal = document.getElementById('btn-open-found-modal');

    // Student Modals & Elements
    const lostModalOverlay = document.getElementById('lost-modal-overlay');
    const btnQuickReport = document.getElementById('btn-quick-report');
    const closeLostModalBtn = document.getElementById('close-lost-modal-btn');
    const cancelLostBtn = document.getElementById('cancel-lost-btn');
    const lostItemForm = document.getElementById('lost-item-form');
    const submitLostBtn = document.getElementById('submit-lost-btn');
    const photoInput = document.getElementById('photo');
    const fileNamePreview = document.getElementById('file-name-preview');

    const foundInfoModalOverlay = document.getElementById('found-info-modal-overlay');
    const closeFoundModalBtn = document.getElementById('close-found-modal-btn');
    const closeFoundInfoBtn = document.getElementById('close-found-info-btn');

    const ticketsGrid = document.getElementById('tickets-grid');
    const filterTabs = document.querySelectorAll('.tab-btn');
    const countAll = document.getElementById('count-all');
    const countOpen = document.getElementById('count-open');
    const countMatched = document.getElementById('count-matched');
    const countResolved = document.getElementById('count-resolved');

    // Staff Modals & Elements
    const staffFoundModalOverlay = document.getElementById('staff-found-modal-overlay');
    const btnStaffQuickLog = document.getElementById('btn-staff-quick-log');
    const closeStaffFoundModalBtn = document.getElementById('close-staff-found-modal-btn');
    const cancelStaffFoundBtn = document.getElementById('cancel-staff-found-btn');
    const staffFoundItemForm = document.getElementById('staff-found-item-form');
    const submitStaffFoundBtn = document.getElementById('submit-staff-found-btn');
    const staffPhotoInput = document.getElementById('staff-photo');
    const staffFileNamePreview = document.getElementById('staff-file-name-preview');

    const staffUpdateModalOverlay = document.getElementById('staff-update-modal-overlay');
    const closeUpdateModalBtn = document.getElementById('close-update-modal-btn');
    const cancelUpdateBtn = document.getElementById('cancel-update-btn');
    const staffUpdateForm = document.getElementById('staff-update-form');
    const submitUpdateBtn = document.getElementById('submit-update-btn');
    const updateModalTitle = document.getElementById('update-modal-title');
    const updateRecordType = document.getElementById('update-record-type');
    const updateRecordId = document.getElementById('update-record-id');
    const updateItemName = document.getElementById('update-item-name');
    const updateCategory = document.getElementById('update-category');
    const updateBrand = document.getElementById('update-brand');
    const updateColor = document.getElementById('update-color');
    const updateLocation = document.getElementById('update-location');
    const updateStatus = document.getElementById('update-status');
    const updateDescription = document.getElementById('update-description');

    // Staff Stats & Tables
    const statFoundCount = document.getElementById('stat-found-count');
    const statMissingCount = document.getElementById('stat-missing-count');
    const statMatchesCount = document.getElementById('stat-matches-count');
    const statReturnedCount = document.getElementById('stat-returned-count');

    const staffTabBtns = document.querySelectorAll('.staff-tab-btn');
    const staffTableSearch = document.getElementById('staff-table-search');
    const tableRecordsInfo = document.getElementById('table-records-info');

    const tableLostItems = document.querySelector('#table-lost-items tbody');
    const tableMissingItems = document.querySelector('#table-missing-items tbody');
    const tableMatches = document.querySelector('#table-matches tbody');
    const tableReturnedItems = document.querySelector('#table-returned-items tbody');

    // Notifications Drawer
    const notifToggleBtn = document.getElementById('notif-toggle-btn');
    const mobileNotifBtn = document.getElementById('mobile-notif-btn');
    const notifDrawer = document.getElementById('notif-drawer');
    const notifOverlay = document.getElementById('notif-overlay');
    const closeNotifBtn = document.getElementById('close-notif-btn');
    const notifList = document.getElementById('notif-list');
    const notifBadge = document.getElementById('notif-badge');
    const mobileNotifBadge = document.getElementById('mobile-notif-badge');
    const markAllReadBtn = document.getElementById('mark-all-read-btn');

    const toastContainer = document.getElementById('toast-container');

    // State Variables
    let currentUser = null;
    let studentTickets = [];
    let currentStudentFilter = 'all';

    let staffLostItems = [];
    let staffMissingTickets = [];
    let staffMatches = [];
    let staffReturnedItems = [];
    let activeStaffTab = 'lost-items';

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

        // Populate user details in navigation
        userDisplayName.textContent = currentUser.full_name.split(' ')[0] || currentUser.username;
        sidebarUserName.textContent = currentUser.full_name;
        sidebarUserRole.textContent = `${currentUser.role.toUpperCase()} (${currentUser.username})`;

        if (currentUser.role === 'staff') {
            userRoleIcon.className = 'fa-solid fa-user-shield';
            setupStaffView();
        } else {
            userRoleIcon.className = 'fa-solid fa-user-graduate';
            setupStudentView();
        }

    } catch (err) {
        console.error('Session check failed:', err);
        window.location.href = '/';
        return;
    }

    // ==========================================
    // 3. Setup Views Based on Role
    // ==========================================

    function setupStudentView() {
        studentSection.style.display = 'block';
        staffSection.style.display = 'none';

        if (btnOpenLostModal) btnOpenLostModal.style.display = 'inline-flex';
        if (heroActionLink) heroActionLink.textContent = 'Track My Report';
        if (navMainLink) navMainLink.textContent = 'My Reports';
        if (sidebarMainLink) sidebarMainLink.textContent = 'My Reports';

        // Student "Found Something?" opens static instructions card
        btnOpenFoundModal.addEventListener('click', () => {
            foundInfoModalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        loadStudentTickets();
    }

    function setupStaffView() {
        studentSection.style.display = 'none';
        staffSection.style.display = 'block';

        // Hide "Lost Something?" hero button for staff (staff only log found items)
        if (btnOpenLostModal) btnOpenLostModal.style.display = 'none';
        if (heroActionLink) {
            heroActionLink.innerHTML = '<i class="fa-solid fa-list-check"></i> Open Management Hub';
        }
        if (navMainLink) navMainLink.textContent = 'Staff Hub';
        if (sidebarMainLink) sidebarMainLink.textContent = 'Staff Hub';

        // Staff "Found Something?" opens functional intake form modal
        btnOpenFoundModal.addEventListener('click', openStaffFoundModal);
        if (btnStaffQuickLog) btnStaffQuickLog.addEventListener('click', openStaffFoundModal);

        loadStaffData();
    }

    // ==========================================
    // 4. Student View Operations
    // ==========================================

    async function loadStudentTickets() {
        try {
            const res = await fetch('/api/tickets/missing', { credentials: 'same-origin' });
            if (!res.ok) throw new Error('Failed to load tickets');

            const data = await res.json();
            studentTickets = data.tickets || [];
            updateStudentCounts();
            renderStudentTickets();
        } catch (err) {
            console.error('Error fetching student tickets:', err);
            ticketsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <p>Unable to load reports. Please try refreshing.</p>
                </div>
            `;
        }
    }

    function updateStudentCounts() {
        countAll.textContent = studentTickets.length;
        countOpen.textContent = studentTickets.filter(t => t.status === 'open').length;
        countMatched.textContent = studentTickets.filter(t => t.status === 'matched').length;
        countResolved.textContent = studentTickets.filter(t => t.status === 'resolved').length;
    }

    function renderStudentTickets() {
        const filtered = currentStudentFilter === 'all'
            ? studentTickets
            : studentTickets.filter(t => t.status === currentStudentFilter);

        if (filtered.length === 0) {
            ticketsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fa-regular fa-clipboard"></i>
                    <p>No ${currentStudentFilter === 'all' ? '' : currentStudentFilter} reports found.</p>
                    <button class="btn btn-yellow" style="margin-top: 14px;" onclick="document.getElementById('btn-open-lost-modal').click()">
                        Report a Missing Item
                    </button>
                </div>
            `;
            return;
        }

        ticketsGrid.innerHTML = filtered.map(t => {
            const statusClass = `status-${t.status}`;
            const statusLabel = t.status === 'open' ? 'Open' :
                                t.status === 'matched' ? 'Match Found' : 'Resolved';

            const photoHtml = t.photo_path
                ? `<img src="${t.photo_path}" alt="${t.item_name}" class="ticket-photo-thumb" loading="lazy">`
                : '';

            const matchCalloutHtml = t.status === 'matched'
                ? `
                <div class="match-alert-callout">
                    <i class="fa-solid fa-bell"></i>
                    <div>
                        <strong>Possible match found!</strong>
                        <p>Please visit the Lost & Found office at Balbago Building for in-person verification.</p>
                    </div>
                </div>
                `
                : '';

            return `
                <div class="ticket-card">
                    <div class="ticket-card-header">
                        <div>
                            <h4 class="ticket-item-name">${escapeHtml(t.item_name)}</h4>
                            <span class="ticket-category-tag">${escapeHtml(t.category)}</span>
                        </div>
                        <span class="status-badge ${statusClass}">${statusLabel}</span>
                    </div>

                    ${t.description ? `<p class="ticket-desc">${escapeHtml(t.description)}</p>` : ''}

                    <ul class="ticket-info-list">
                        <li>
                            <i class="fa-regular fa-calendar"></i>
                            <span>Lost: <strong>${escapeHtml(t.date_lost)}</strong> ${t.time_lost ? `(${escapeHtml(t.time_lost)})` : ''}</span>
                        </li>
                        <li>
                            <i class="fa-solid fa-location-dot"></i>
                            <span>Location: <strong>${escapeHtml(t.locations)}</strong></span>
                        </li>
                        ${t.color || t.brand ? `
                        <li>
                            <i class="fa-solid fa-tag"></i>
                            <span>${t.brand ? `Brand: <strong>${escapeHtml(t.brand)}</strong> ` : ''}${t.color ? `Color: <strong>${escapeHtml(t.color)}</strong>` : ''}</span>
                        </li>
                        ` : ''}
                    </ul>

                    ${photoHtml}
                    ${matchCalloutHtml}

                    <div class="ticket-footer">
                        <span>Report #${t.id}</span>
                        <span>Filed: ${formatDate(t.created_at)}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Student Filter Tabs
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentStudentFilter = tab.getAttribute('data-filter');
            renderStudentTickets();
        });
    });

    // Student Lost Form Handlers
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
                await loadStudentTickets();
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

    // Student Found Info Modal
    function closeFoundInfoModal() {
        foundInfoModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (closeFoundModalBtn) closeFoundModalBtn.addEventListener('click', closeFoundInfoModal);
    if (closeFoundInfoBtn) closeFoundInfoBtn.addEventListener('click', closeFoundInfoModal);
    foundInfoModalOverlay.addEventListener('click', (e) => {
        if (e.target === foundInfoModalOverlay) closeFoundInfoModal();
    });

    // ==========================================
    // 5. Staff View Operations
    // ==========================================

    async function loadStaffData() {
        await Promise.all([
            fetchStaffLostItems(),
            fetchStaffMissingTickets(),
            fetchStaffMatches(),
            fetchStaffReturnedItems()
        ]);
        updateStaffStats();
        renderStaffTables();
    }

    async function fetchStaffLostItems() {
        try {
            const res = await fetch('/api/tickets/lost', { credentials: 'same-origin' });
            if (res.ok) {
                const data = await res.json();
                staffLostItems = data.items || [];
            }
        } catch (e) {
            console.error('Error fetching lost items:', e);
        }
    }

    async function fetchStaffMissingTickets() {
        try {
            const res = await fetch('/api/tickets/missing', { credentials: 'same-origin' });
            if (res.ok) {
                const data = await res.json();
                staffMissingTickets = data.tickets || [];
            }
        } catch (e) {
            console.error('Error fetching missing tickets:', e);
        }
    }

    async function fetchStaffMatches() {
        try {
            const res = await fetch('/api/matches', { credentials: 'same-origin' });
            if (res.ok) {
                const data = await res.json();
                staffMatches = data.matches || [];
            }
        } catch (e) {
            console.error('Error fetching matches:', e);
        }
    }

    async function fetchStaffReturnedItems() {
        try {
            const res = await fetch('/api/tickets/returned', { credentials: 'same-origin' });
            if (res.ok) {
                const data = await res.json();
                staffReturnedItems = data.items || [];
            }
        } catch (e) {
            console.error('Error fetching returned items:', e);
        }
    }

    function updateStaffStats() {
        statFoundCount.textContent = staffLostItems.length;
        statMissingCount.textContent = staffMissingTickets.length;
        statMatchesCount.textContent = staffMatches.filter(m => m.match_status === 'pending').length;
        statReturnedCount.textContent = staffReturnedItems.length;
    }

    // Tab Switching for Staff Tables
    staffTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            staffTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeStaffTab = btn.getAttribute('data-tab');

            document.querySelectorAll('.table-pane').forEach(p => p.classList.remove('active'));
            document.getElementById(`pane-${activeStaffTab}`).classList.add('active');

            filterAndRenderActiveStaffTable();
        });
    });

    if (staffTableSearch) {
        staffTableSearch.addEventListener('input', () => {
            filterAndRenderActiveStaffTable();
        });
    }

    function renderStaffTables() {
        filterAndRenderActiveStaffTable();
    }

    function filterAndRenderActiveStaffTable() {
        const query = (staffTableSearch ? staffTableSearch.value : '').toLowerCase().trim();

        if (activeStaffTab === 'lost-items') {
            const filtered = staffLostItems.filter(item => 
                !query ||
                item.item_name.toLowerCase().includes(query) ||
                item.category.toLowerCase().includes(query) ||
                (item.location_found && item.location_found.toLowerCase().includes(query)) ||
                (item.brand && item.brand.toLowerCase().includes(query)) ||
                (item.color && item.color.toLowerCase().includes(query))
            );
            tableRecordsInfo.textContent = `Showing ${filtered.length} of ${staffLostItems.length} found items`;
            renderLostItemsTable(filtered);

        } else if (activeStaffTab === 'missing-items') {
            const filtered = staffMissingTickets.filter(t => 
                !query ||
                t.item_name.toLowerCase().includes(query) ||
                t.student_name.toLowerCase().includes(query) ||
                t.student_id_number.toLowerCase().includes(query) ||
                t.category.toLowerCase().includes(query) ||
                (t.locations && t.locations.toLowerCase().includes(query))
            );
            tableRecordsInfo.textContent = `Showing ${filtered.length} of ${staffMissingTickets.length} missing reports`;
            renderMissingItemsTable(filtered);

        } else if (activeStaffTab === 'matches-verif') {
            const filtered = staffMatches.filter(m => 
                !query ||
                m.missing_item_name.toLowerCase().includes(query) ||
                m.lost_item_name.toLowerCase().includes(query) ||
                m.student_name.toLowerCase().includes(query) ||
                m.student_id_number.toLowerCase().includes(query)
            );
            tableRecordsInfo.textContent = `Showing ${filtered.length} of ${staffMatches.length} matches`;
            renderMatchesTable(filtered);

        } else if (activeStaffTab === 'returned-items') {
            const filtered = staffReturnedItems.filter(item => 
                !query ||
                item.item_name.toLowerCase().includes(query) ||
                item.category.toLowerCase().includes(query) ||
                (item.location_found && item.location_found.toLowerCase().includes(query))
            );
            tableRecordsInfo.textContent = `Showing ${filtered.length} of ${staffReturnedItems.length} returned items`;
            renderReturnedItemsTable(filtered);
        }
    }

    function renderLostItemsTable(items) {
        if (items.length === 0) {
            tableLostItems.innerHTML = `<tr><td colspan="7" class="table-empty">No found items logged yet.</td></tr>`;
            return;
        }

        tableLostItems.innerHTML = items.map(item => `
            <tr>
                <td><strong>#${item.id}</strong></td>
                <td>
                    <strong>${escapeHtml(item.item_name)}</strong>
                    ${item.brand ? `<br><small class="text-muted">Brand: ${escapeHtml(item.brand)}</small>` : ''}
                </td>
                <td><span class="ticket-category-tag">${escapeHtml(item.category)}</span></td>
                <td>${escapeHtml(item.date_found)}</td>
                <td>${escapeHtml(item.location_found)}</td>
                <td><span class="status-badge status-${item.status}">${item.status.replace('_', ' ')}</span></td>
                <td>
                    <div class="action-btn-group">
                        <button class="btn-table-action btn-action-edit" onclick="openStaffUpdateModal('lost', ${item.id})">
                            <i class="fa-solid fa-pen-to-square"></i> Update
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    function renderMissingItemsTable(tickets) {
        if (tickets.length === 0) {
            tableMissingItems.innerHTML = `<tr><td colspan="8" class="table-empty">No missing reports on record.</td></tr>`;
            return;
        }

        tableMissingItems.innerHTML = tickets.map(t => `
            <tr>
                <td><strong>#${t.id}</strong></td>
                <td><code>${escapeHtml(t.student_id_number)}</code></td>
                <td>${escapeHtml(t.student_name)}</td>
                <td><strong>${escapeHtml(t.item_name)}</strong></td>
                <td><span class="ticket-category-tag">${escapeHtml(t.category)}</span></td>
                <td>${escapeHtml(t.date_lost)}</td>
                <td><span class="status-badge status-${t.status}">${t.status}</span></td>
                <td>
                    <div class="action-btn-group">
                        <button class="btn-table-action btn-action-edit" onclick="openStaffUpdateModal('missing', ${t.id})">
                            <i class="fa-solid fa-pen-to-square"></i> Update
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    function renderMatchesTable(matches) {
        if (matches.length === 0) {
            tableMatches.innerHTML = `<tr><td colspan="6" class="table-empty">No match comparisons currently recorded.</td></tr>`;
            return;
        }

        tableMatches.innerHTML = matches.map(m => {
            const isPending = m.match_status === 'pending';
            const actionButtons = isPending ? `
                <div class="action-btn-group">
                    <button class="btn-table-action btn-action-verify" onclick="verifyMatch(${m.match_id})">
                        <i class="fa-solid fa-check"></i> Verify & Claim
                    </button>
                    <button class="btn-table-action btn-action-reject" onclick="rejectMatch(${m.match_id})">
                        <i class="fa-solid fa-xmark"></i> Reject
                    </button>
                </div>
            ` : `<span class="status-badge status-${m.match_status}">${m.match_status}</span>`;

            return `
                <tr>
                    <td><strong>#M-${m.match_id}</strong></td>
                    <td>
                        <strong>${escapeHtml(m.missing_item_name)}</strong><br>
                        <small>Student: ${escapeHtml(m.student_name)} (<code>${escapeHtml(m.student_id_number)}</code>)</small>
                    </td>
                    <td>
                        <strong>${escapeHtml(m.lost_item_name)}</strong> (Item #${m.lost_item_id})<br>
                        <small>Found: ${escapeHtml(m.location_found)} (${escapeHtml(m.date_found)})</small>
                    </td>
                    <td><span class="score-badge">${Math.round(m.match_score * 100)}% match</span></td>
                    <td><span class="status-badge status-${m.match_status}">${m.match_status}</span></td>
                    <td>${actionButtons}</td>
                </tr>
            `;
        }).join('');
    }

    function renderReturnedItemsTable(items) {
        if (items.length === 0) {
            tableReturnedItems.innerHTML = `<tr><td colspan="7" class="table-empty">No items marked as returned yet.</td></tr>`;
            return;
        }

        tableReturnedItems.innerHTML = items.map(item => `
            <tr>
                <td><strong>#${item.id}</strong></td>
                <td><strong>${escapeHtml(item.item_name)}</strong></td>
                <td><span class="ticket-category-tag">${escapeHtml(item.category)}</span></td>
                <td>${escapeHtml(item.date_found)}</td>
                <td>${escapeHtml(item.location_found)}</td>
                <td>${escapeHtml(item.logged_by_name || 'Staff')}</td>
                <td><span class="status-badge status-resolved">Claimed</span></td>
            </tr>
        `).join('');
    }

    // Staff Found Item Logging Form Handlers
    function openStaffFoundModal() {
        staffFoundModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        document.getElementById('staff-date-found').value = new Date().toISOString().split('T')[0];
    }

    function closeStaffFoundModal() {
        staffFoundModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        staffFoundItemForm.reset();
        staffFileNamePreview.textContent = '';
    }

    if (closeStaffFoundModalBtn) closeStaffFoundModalBtn.addEventListener('click', closeStaffFoundModal);
    if (cancelStaffFoundBtn) cancelStaffFoundBtn.addEventListener('click', closeStaffFoundModal);
    staffFoundModalOverlay.addEventListener('click', (e) => {
        if (e.target === staffFoundModalOverlay) closeStaffFoundModal();
    });

    staffPhotoInput.addEventListener('change', () => {
        if (staffPhotoInput.files.length > 0) {
            const file = staffPhotoInput.files[0];
            if (file.size > 5 * 1024 * 1024) {
                showToast('File size exceeds 5 MB limit.', 'error');
                staffPhotoInput.value = '';
                staffFileNamePreview.textContent = '';
                return;
            }
            staffFileNamePreview.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        } else {
            staffFileNamePreview.textContent = '';
        }
    });

    staffFoundItemForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtnText = submitStaffFoundBtn.innerHTML;
        submitStaffFoundBtn.disabled = true;
        submitStaffFoundBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving & Matching...';

        try {
            const formData = new FormData(staffFoundItemForm);
            const res = await fetch('/api/tickets/lost', {
                method: 'POST',
                credentials: 'same-origin',
                body: formData
            });

            const data = await res.json();
            if (res.ok) {
                closeStaffFoundModal();
                if (data.matches_found > 0) {
                    showToast(`Item logged! ${data.matches_found} student match found. Match status updated!`, 'success');
                } else {
                    showToast('Found item logged into inventory successfully.', 'success');
                }
                await loadStaffData();
                await loadNotifications();
            } else {
                showToast(data.detail || 'Failed to log found item.', 'error');
            }
        } catch (err) {
            console.error('Error logging found item:', err);
            showToast('Network error. Please try again.', 'error');
        } finally {
            submitStaffFoundBtn.disabled = false;
            submitStaffFoundBtn.innerHTML = submitBtnText;
        }
    });

    // In-Person Verification & Rejection Actions
    window.verifyMatch = async function(matchId) {
        if (!confirm('Confirm in-person verification? This will mark the found item as CLAIMED and resolve the student missing ticket.')) {
            return;
        }

        try {
            const res = await fetch(`/api/matches/${matchId}/verify`, {
                method: 'PUT',
                credentials: 'same-origin'
            });

            if (res.ok) {
                showToast('Ownership verified! Item claimed and ticket resolved.', 'success');
                await loadStaffData();
                await loadNotifications();
            } else {
                const data = await res.json();
                showToast(data.detail || 'Failed to verify match.', 'error');
            }
        } catch (err) {
            console.error('Verification error:', err);
            showToast('Error verifying match.', 'error');
        }
    };

    window.rejectMatch = async function(matchId) {
        if (!confirm('Reject this match? (The student report will remain open if no other matches exist).')) {
            return;
        }

        try {
            const res = await fetch(`/api/matches/${matchId}/reject`, {
                method: 'PUT',
                credentials: 'same-origin'
            });

            if (res.ok) {
                showToast('Match marked as rejected.', 'info');
                await loadStaffData();
            } else {
                const data = await res.json();
                showToast(data.detail || 'Failed to reject match.', 'error');
            }
        } catch (err) {
            console.error('Rejection error:', err);
            showToast('Error rejecting match.', 'error');
        }
    };

    // Staff Update Modal (Update Only - Strictly No Delete)
    window.openStaffUpdateModal = function(type, id) {
        updateRecordType.value = type;
        updateRecordId.value = id;

        if (type === 'lost') {
            const item = staffLostItems.find(i => i.id === id);
            if (!item) return;

            updateModalTitle.textContent = `Update Found Item #${item.id}`;
            updateItemName.value = item.item_name;
            updateCategory.value = item.category;
            updateBrand.value = item.brand || '';
            updateColor.value = item.color || '';
            updateLocation.value = item.location_found;
            updateDescription.value = item.description || '';

            updateStatus.innerHTML = `
                <option value="unclaimed" ${item.status === 'unclaimed' ? 'selected' : ''}>Unclaimed</option>
                <option value="pending_verification" ${item.status === 'pending_verification' ? 'selected' : ''}>Pending Verification</option>
                <option value="claimed" ${item.status === 'claimed' ? 'selected' : ''}>Claimed</option>
            `;

        } else if (type === 'missing') {
            const ticket = staffMissingTickets.find(t => t.id === id);
            if (!ticket) return;

            updateModalTitle.textContent = `Update Missing Report #${ticket.id}`;
            updateItemName.value = ticket.item_name;
            updateCategory.value = ticket.category;
            updateBrand.value = ticket.brand || '';
            updateColor.value = ticket.color || '';
            updateLocation.value = ticket.locations;
            updateDescription.value = ticket.description || '';

            updateStatus.innerHTML = `
                <option value="open" ${ticket.status === 'open' ? 'selected' : ''}>Open</option>
                <option value="matched" ${ticket.status === 'matched' ? 'selected' : ''}>Matched</option>
                <option value="resolved" ${ticket.status === 'resolved' ? 'selected' : ''}>Resolved</option>
            `;
        }

        staffUpdateModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    };

    function closeStaffUpdateModal() {
        staffUpdateModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        staffUpdateForm.reset();
    }

    if (closeUpdateModalBtn) closeUpdateModalBtn.addEventListener('click', closeStaffUpdateModal);
    if (cancelUpdateBtn) cancelUpdateBtn.addEventListener('click', closeStaffUpdateModal);
    staffUpdateModalOverlay.addEventListener('click', (e) => {
        if (e.target === staffUpdateModalOverlay) closeStaffUpdateModal();
    });

    staffUpdateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const type = updateRecordType.value;
        const id = updateRecordId.value;

        const submitBtnText = submitUpdateBtn.innerHTML;
        submitUpdateBtn.disabled = true;
        submitUpdateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        const payload = {
            item_name: updateItemName.value.trim(),
            category: updateCategory.value,
            brand: updateBrand.value.trim() || null,
            color: updateColor.value.trim() || null,
            description: updateDescription.value.trim() || null,
            status: updateStatus.value
        };

        if (type === 'lost') {
            payload.location_found = updateLocation.value.trim();
        } else {
            payload.locations = updateLocation.value.trim();
        }

        const endpoint = type === 'lost' ? `/api/tickets/lost/${id}` : `/api/tickets/missing/${id}`;

        try {
            const res = await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                closeStaffUpdateModal();
                showToast('Record updated successfully.', 'success');
                await loadStaffData();
            } else {
                const data = await res.json();
                showToast(data.detail || 'Failed to update record.', 'error');
            }
        } catch (err) {
            console.error('Update record error:', err);
            showToast('Network error. Please try again.', 'error');
        } finally {
            submitUpdateBtn.disabled = false;
            submitUpdateBtn.innerHTML = submitBtnText;
        }
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

    // Initial notification load
    await loadNotifications();
});
