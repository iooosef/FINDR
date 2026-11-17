/**
 * script.js - Frontend authentication logic for FINDR.
 * Connects the Sign-In and Sign-Up forms to the FastAPI backend.
 */

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('container');
    const registerBtn = document.getElementById('register');
    const loginBtn = document.getElementById('login');

    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');

    const signinAlert = document.getElementById('signin-alert');
    const signupAlert = document.getElementById('signup-alert');

    const signinSubmitBtn = document.getElementById('signin-submit-btn');
    const signupSubmitBtn = document.getElementById('signup-submit-btn');

    // ==========================================
    // 1. Sliding Panel Toggle
    // ==========================================

    registerBtn.addEventListener('click', () => {
        container.classList.add('active');
        clearAlert(signinAlert);
    });

    loginBtn.addEventListener('click', () => {
        container.classList.remove('active');
        clearAlert(signupAlert);
    });

    // ==========================================
    // 2. Alert Helper Functions
    // ==========================================

    function showAlert(element, message, type = 'error') {
        element.className = `alert-box ${type}`;
        element.innerHTML = `
            <i class="fa-solid ${type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'}"></i>
            <span>${message}</span>
        `;
        element.style.display = 'flex';
    }

    function clearAlert(element) {
        if (element) {
            element.style.display = 'none';
            element.innerHTML = '';
        }
    }

    // ==========================================
    // 3. Auto-redirect if already logged in
    // ==========================================

    async function checkExistingSession() {
        try {
            const res = await fetch('/api/auth/me', { credentials: 'same-origin' });
            if (res.ok) {
                // User already has an active session cookie
                window.location.href = '/dashboard';
            }
        } catch (err) {
            // Server offline or network error; keep user on login page
            console.debug('Session check skipped:', err);
        }
    }

    checkExistingSession();

    // ==========================================
    // 4. Handle Sign In (Student & Staff)
    // ==========================================

    signinForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert(signinAlert);

        const idNumber = document.getElementById('signin-idnumber').value.trim();
        const password = document.getElementById('signin-password').value;

        if (!idNumber || !password) {
            showAlert(signinAlert, 'Please fill in all fields.', 'error');
            return;
        }

        // Set button loading state
        const originalBtnText = signinSubmitBtn.innerHTML;
        signinSubmitBtn.disabled = true;
        signinSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Signing In...</span>';

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    id_number: idNumber,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                showAlert(signinAlert, 'Login successful! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 500);
            } else {
                const errorMsg = data.detail || 'Invalid ID number or password.';
                showAlert(signinAlert, errorMsg, 'error');
            }
        } catch (error) {
            console.error('Sign In Error:', error);
            showAlert(signinAlert, 'Unable to connect to server. Please try again.', 'error');
        } finally {
            signinSubmitBtn.disabled = false;
            signinSubmitBtn.innerHTML = originalBtnText;
        }
    });

    // ==========================================
    // 5. Handle Sign Up (Students)
    // ==========================================

    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearAlert(signupAlert);

        const name = document.getElementById('name-input').value.trim();
        const idNumber = document.getElementById('idnumber-input').value.trim();
        const password = document.getElementById('password-input').value;

        if (!name || !idNumber || !password) {
            showAlert(signupAlert, 'Please complete all required fields.', 'error');
            return;
        }

        if (password.length < 4) {
            showAlert(signupAlert, 'Password must be at least 4 characters long.', 'error');
            return;
        }

        // Set button loading state
        const originalBtnText = signupSubmitBtn.innerHTML;
        signupSubmitBtn.disabled = true;
        signupSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Creating Account...</span>';

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    name: name,
                    id_number: idNumber,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                showAlert(signupAlert, 'Account created! Redirecting to dashboard...', 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 600);
            } else {
                const errorMsg = data.detail || 'Registration failed. Please check your details.';
                showAlert(signupAlert, errorMsg, 'error');
            }
        } catch (error) {
            console.error('Sign Up Error:', error);
            showAlert(signupAlert, 'Unable to connect to server. Please try again.', 'error');
        } finally {
            signupSubmitBtn.disabled = false;
            signupSubmitBtn.innerHTML = originalBtnText;
        }
    });
});
